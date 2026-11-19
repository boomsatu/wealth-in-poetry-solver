/*
 * gpu_solver.cu  —  Full-pipeline Dual RTX 5090 Dispersal Solver
 *
 * Pipeline:
 *   GPU : Candidate decode (12-block Cartesian) + Real SHA-256 BIP-39 checksum filter
 *   CPU : Thread-pool PBKDF2-HMAC-SHA512 (2048 iter) + BIP-32/BIP-44 derivation
 *         + secp256k1 pubkey + Hash160 (SHA-256+RIPEMD-160) + address compare
 *
 * Fix v3: Double-buffering (GPU/CPU overlap) + CPU thread pool (all cores)
 *         + correct MAX_VALID to prevent buffer overflow
 *
 * Compile (on GPU server):
 *   nvcc -O3 -std=c++17 -arch=native gpu_solver.cu -o gpu_solver \
 *        -lssl -lcrypto -lpthread
 */

/* ============================================================
 * Standard includes
 * ============================================================ */
#include <cuda_runtime.h>
#include <device_launch_parameters.h>

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <atomic>
#include <chrono>
#include <condition_variable>
#include <future>
#include <mutex>
#include <queue>
#include <thread>
#include <vector>

/* OpenSSL (host-side crypto) */
#include <openssl/evp.h>
#include <openssl/hmac.h>
#include <openssl/ripemd.h>
#include <openssl/sha.h>
/* secp256k1 via OpenSSL EC */
#include <openssl/bn.h>
#include <openssl/ec.h>
#include <openssl/obj_mac.h>

/* ============================================================
 * Target constants
 * ============================================================ */
static const char TARGET_ADDR[] = "1K4ezpLybootYF23TM4a8Y4NyP7auysnRo";
static const uint8_t TARGET_H160[20] = {
    0xc6,0x23,0x3a,0xeb,0x3a,0x50,0xa7,0x0b,
    0x82,0xfc,0xd8,0x8d,0x69,0xb5,0xf1,0xa3,
    0xec,0x6e,0x35,0x5a
};

/* ============================================================
 * 12-Block Dispersal data  (GPU constant memory)
 * ============================================================ */
__constant__ int      d_bsz[12]     = {10,7,7,13,8,8,4,10,12,7,12,13};
__constant__ uint16_t d_bwrd[12][16] = {
    {935,1004,646,545,532,1785,439,1754,1261,663},
    {58,1572,331,2038,1999,1785,1612},
    {1162,650,715,1302,532,1770,1785},
    {786,613,1004,1076,1500,2012,856,1832,517,650,2004,786,1600},
    {856,1891,1785,786,1406,664,331,201},
    {396,786,1785,160,1863,67,1548,331},
    {1284,287,2004,1898},
    {1302,1234,1261,1032,735,2010,102,1265,1754,102},
    {1265,650,786,856,1162,1762,1222,1195,2046,1785,1698,786},
    {160,935,1194,829,1904,1605,1234},
    {191,786,401,0,863,646,400,1605,1028,1861,1234,35},
    {1899,863,1193,1162,35,1374,431,1770,1710,1698,1787,1221,843}
};

/* ============================================================
 * Device SHA-256  (single 16-byte input → first output byte)
 * ============================================================ */
#define ROTR(x,n) (((x)>>(n))|((x)<<(32-(n))))
#define SHR(x,n)  ((x)>>(n))
#define CH(x,y,z) (((x)&(y))^(~(x)&(z)))
#define MAJ(x,y,z)(((x)&(y))^((x)&(z))^((y)&(z)))
#define EP0(x) (ROTR(x,2)^ROTR(x,13)^ROTR(x,22))
#define EP1(x) (ROTR(x,6)^ROTR(x,11)^ROTR(x,25))
#define SG0(x) (ROTR(x,7)^ROTR(x,18)^SHR(x,3))
#define SG1(x) (ROTR(x,17)^ROTR(x,19)^SHR(x,10))

__device__ __constant__ uint32_t K256[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,
    0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,
    0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,
    0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,
    0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,
    0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,
    0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,
    0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,
    0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};

__device__ __forceinline__ uint8_t sha256_16b_firstbyte(const uint8_t* d) {
    uint32_t h0=0x6a09e667, h1=0xbb67ae85, h2=0x3c6ef372, h3=0xa54ff53a;
    uint32_t h4=0x510e527f, h5=0x9b05688c, h6=0x1f83d9ab, h7=0x5be0cd19;

    uint32_t W[64];
    for (int i=0;i<4;i++)
        W[i] = ((uint32_t)d[i*4]<<24)|((uint32_t)d[i*4+1]<<16)|
               ((uint32_t)d[i*4+2]<<8)|(uint32_t)d[i*4+3];
    W[4]=0x80000000;
    for (int i=5;i<15;i++) W[i]=0;
    W[15]=0x00000080;

    for (int i=16;i<64;i++)
        W[i]=SG1(W[i-2])+W[i-7]+SG0(W[i-15])+W[i-16];

    uint32_t a=h0,b=h1,c=h2,d2=h3,e=h4,f=h5,g=h6,hh=h7;
    for (int i=0;i<64;i++){
        uint32_t T1=hh+EP1(e)+CH(e,f,g)+K256[i]+W[i];
        uint32_t T2=EP0(a)+MAJ(a,b,c);
        hh=g; g=f; f=e; e=d2+T1;
        d2=c; c=b; b=a; a=T1+T2;
    }
    return (uint8_t)((h0+a)>>24);
}

__device__ __forceinline__ int real_bip39_check(const uint16_t* idx) {
    uint8_t bits[17]={0};
    int bp=0;
    for (int i=0;i<12;i++){
        uint16_t v=idx[i];
        for (int b=10;b>=0;b--){
            uint8_t bit=(v>>b)&1;
            bits[bp/8]|=(bit<<(7-(bp%8)));
            bp++;
        }
    }
    uint8_t expected=(bits[16]>>4)&0x0F;
    uint8_t actual  =(sha256_16b_firstbyte(bits)>>4)&0x0F;
    return (expected==actual)?1:0;
}

/* ============================================================
 * GPU kernel
 * MAX_VALID sized for batch=500K: 500K*7% = 35000 → 65536 safe margin
 * ============================================================ */
#define BATCH_SIZE  500000ULL   /* 500K per kernel — avoids buffer overflow  */
#define MAX_VALID   65536       /* 500K * 6.25% * 2 safety = 62500 → 65536  */

__global__ void dispersal_kernel(
    uint64_t base_id,
    uint64_t count,
    volatile uint32_t* __restrict__ g_stop,
    uint16_t*          __restrict__ g_valid_buf,
    volatile uint32_t* __restrict__ g_valid_cnt
){
    uint64_t tid = (uint64_t)blockDim.x*blockIdx.x + threadIdx.x;
    if (tid>=count || *g_stop) return;

    uint64_t id=base_id+tid;
    uint16_t cand[12];
    uint64_t rem=id;
    for (int b=11;b>=0;b--){
        int sz=d_bsz[b];
        cand[b]=d_bwrd[b][rem%sz];
        rem/=sz;
    }

    if (real_bip39_check(cand)){
        uint32_t slot=atomicAdd((uint32_t*)g_valid_cnt,1u);
        if (slot<MAX_VALID){
            uint16_t* dst=g_valid_buf+slot*12;
            for (int i=0;i<12;i++) dst[i]=cand[i];
        }
    }
}

/* ============================================================
 * Host crypto (OpenSSL)
 * ============================================================ */
static const char* WL[2048];
static bool wl_ok=false;

static bool load_wordlist(){
    const char* paths[]={"../../english.txt","../english.txt","english.txt",nullptr};
    for (int pi=0;paths[pi];pi++){
        FILE* f=fopen(paths[pi],"r");
        if (!f) continue;
        char buf[64]; int n=0;
        while (n<2048 && fgets(buf,sizeof(buf),f)){
            int L=strlen(buf);
            while (L>0&&(buf[L-1]=='\n'||buf[L-1]=='\r')) buf[--L]=0;
            WL[n++]=strdup(buf);
        }
        fclose(f);
        if (n==2048){ wl_ok=true; return true; }
    }
    return false;
}

static void indices_to_phrase(const uint16_t* idx, char* out, size_t cap){
    out[0]=0;
    for (int i=0;i<12;i++){
        if (i) strncat(out," ",cap-1);
        strncat(out,WL[idx[i]],cap-1);
    }
}

static void phrase_to_seed(const char* phrase, uint8_t seed[64]){
    const char salt[]="mnemonic";
    PKCS5_PBKDF2_HMAC(phrase,(int)strlen(phrase),
                      (const uint8_t*)salt,(int)strlen(salt),
                      2048,EVP_sha512(),64,seed);
}

static void hmac512(const uint8_t* key,int klen,
                    const uint8_t* data,int dlen,
                    uint8_t out[64]){
    unsigned int olen=64;
    HMAC(EVP_sha512(),key,klen,data,dlen,out,&olen);
}

static const uint8_t N32[32]={
    0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,
    0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xfe,
    0xba,0xae,0xdc,0xe6,0xaf,0x48,0xa0,0x3b,
    0xbf,0xd2,0x5e,0x8c,0xd0,0x36,0x41,0x41
};

struct XKey { uint8_t prv[32], chn[32]; };

static XKey master_from_seed(const uint8_t* seed){
    XKey k; uint8_t I[64];
    hmac512((uint8_t*)"Bitcoin seed",12,seed,64,I);
    memcpy(k.prv,I,32); memcpy(k.chn,I+32,32);
    return k;
}

static bool pubkey33(const uint8_t* prv32, uint8_t* pub33){
    EC_GROUP* G=EC_GROUP_new_by_curve_name(NID_secp256k1);
    if (!G) return false;
    BIGNUM* bn=BN_bin2bn(prv32,32,NULL);
    EC_POINT* P=EC_POINT_new(G);
    EC_POINT_mul(G,P,bn,NULL,NULL,NULL);
    BN_CTX* ctx=BN_CTX_new();
    size_t len=EC_POINT_point2oct(G,P,POINT_CONVERSION_COMPRESSED,pub33,33,ctx);
    BN_free(bn); EC_POINT_free(P); EC_GROUP_free(G); BN_CTX_free(ctx);
    return len==33;
}

static void hash160(const uint8_t* data, int dlen, uint8_t h160[20]){
    uint8_t sha[32];
    SHA256(data,dlen,sha);
    RIPEMD160(sha,32,h160);
}

static bool child(const XKey& par, uint32_t idx, bool hard, XKey& out){
    uint8_t data[37];
    uint32_t i32=hard?(idx|0x80000000u):idx;
    if (hard){ data[0]=0x00; memcpy(data+1,par.prv,32); }
    else { uint8_t pub[33]; if (!pubkey33(par.prv,pub)) return false; memcpy(data,pub,33); }
    data[33]=(i32>>24)&0xFF; data[34]=(i32>>16)&0xFF;
    data[35]=(i32>>8)&0xFF;  data[36]=i32&0xFF;
    uint8_t I[64]; hmac512(par.chn,32,data,37,I);
    BIGNUM* il=BN_bin2bn(I,32,NULL); BIGNUM* pk=BN_bin2bn(par.prv,32,NULL);
    BIGNUM* n=BN_bin2bn(N32,32,NULL); BIGNUM* ck=BN_new(); BN_CTX* ctx=BN_CTX_new();
    BN_mod_add(ck,il,pk,n,ctx);
    bool ok=!BN_is_zero(ck);
    BN_bn2binpad(ck,out.prv,32); memcpy(out.chn,I+32,32);
    BN_free(il); BN_free(pk); BN_free(n); BN_free(ck); BN_CTX_free(ctx);
    return ok;
}

static bool verify_one(const uint16_t* indices, char* phrase_out, char* path_out){
    if (!wl_ok) return false;
    char phrase[256]; indices_to_phrase(indices,phrase,sizeof(phrase));
    uint8_t seed[64]; phrase_to_seed(phrase,seed);
    XKey M=master_from_seed(seed);

    auto check=[&](const uint8_t* prv, const char* path)->bool{
        uint8_t pub[33],h160[20];
        if (!pubkey33(prv,pub)) return false;
        hash160(pub,33,h160);
        if (!memcmp(h160,TARGET_H160,20)){
            strcpy(phrase_out,phrase); strcpy(path_out,path); return true; }
        return false;
    };

    if (check(M.prv,"m")) return true;

    XKey a,b,c2,ext,leaf;
    // m/44'/0'/0'/0/i
    if (child(M,44,true,a)&&child(a,0,true,b)&&child(b,0,true,c2)&&child(c2,0,false,ext))
        for (uint32_t i=0;i<10;i++){
            if (!child(ext,i,false,leaf)) continue;
            char p[32]; sprintf(p,"m/44'/0'/0'/0/%u",i);
            if (check(leaf.prv,p)) return true;
        }
    // m/44'/0'/0'/1/i (change)
    if (child(M,44,true,a)&&child(a,0,true,b)&&child(b,0,true,c2)&&child(c2,1,false,ext))
        for (uint32_t i=0;i<5;i++){
            if (!child(ext,i,false,leaf)) continue;
            char p[32]; sprintf(p,"m/44'/0'/0'/1/%u",i);
            if (check(leaf.prv,p)) return true;
        }
    // m/0/i (Electrum)
    if (child(M,0,false,a))
        for (uint32_t i=0;i<5;i++){
            if (!child(a,i,false,leaf)) continue;
            char p[16]; sprintf(p,"m/0/%u",i);
            if (check(leaf.prv,p)) return true;
        }
    return false;
}

/* ============================================================
 * Shared counters & thread-safe verify-queue
 * ============================================================ */
static std::atomic<uint64_t> G_generated(0);
static std::atomic<uint64_t> G_cs_pass(0);
static std::atomic<uint64_t> G_verified(0);
static std::atomic<bool>     G_found(false);

/* Bounded verification queue — prevents memory blowup */
struct VerifyQueue {
    static const size_t MAX_Q = 2000000; /* 2M slots max in queue */
    std::queue<std::vector<uint16_t>> q_;
    std::mutex mtx_;
    std::condition_variable cv_not_empty_, cv_not_full_;
    bool done_ = false;

    /* Push a batch of candidates (blocks until space available) */
    void push(const uint16_t* buf, uint32_t n){
        std::unique_lock<std::mutex> lk(mtx_);
        cv_not_full_.wait(lk,[&]{ return q_.size()+n<=MAX_Q || done_; });
        for (uint32_t i=0;i<n;i++){
            std::vector<uint16_t> v(buf+i*12, buf+i*12+12);
            q_.push(std::move(v));
        }
        cv_not_empty_.notify_all();
    }

    /* Pop one candidate; returns false when queue empty + done */
    bool pop(std::vector<uint16_t>& out){
        std::unique_lock<std::mutex> lk(mtx_);
        cv_not_empty_.wait(lk,[&]{ return !q_.empty() || done_; });
        if (q_.empty()) return false;
        out=std::move(q_.front()); q_.pop();
        cv_not_full_.notify_one();
        return true;
    }

    void set_done(){
        std::unique_lock<std::mutex> lk(mtx_);
        done_=true;
        cv_not_empty_.notify_all();
        cv_not_full_.notify_all();
    }

    size_t size(){
        std::unique_lock<std::mutex> lk(mtx_);
        return q_.size();
    }
} G_queue;

/* CPU verifier thread: pulls from queue, runs PBKDF2+BIP44 */
static void cpu_verifier_thread(){
    std::vector<uint16_t> cand;
    while (G_queue.pop(cand)){
        if (G_found.load()) { G_verified.fetch_add(1); continue; }
        char phrase[256]="", path[64]="";
        if (verify_one(cand.data(), phrase, path)){
            G_found.store(true);
            printf("\n");
            printf("============================================================\n");
            printf("  TARGET FOUND!\n");
            printf("  Mnemonic : %s\n", phrase);
            printf("  Path     : %s\n", path);
            printf("  Address  : %s\n", TARGET_ADDR);
            printf("============================================================\n");
            fflush(stdout);
        }
        G_verified.fetch_add(1);
    }
}

/* ============================================================
 * Per-GPU worker — pushes to queue, doesn't wait for CPU
 * ============================================================ */
static void gpu_worker(int dev, uint64_t base, uint64_t total,
                       std::chrono::time_point<std::chrono::high_resolution_clock> t_global_start){
    cudaSetDevice(dev);
    cudaDeviceProp p; cudaGetDeviceProperties(&p,dev);
    printf("[GPU %d] %s  SMs=%d  VRAM=%.1fGB\n",
           dev,p.name,p.multiProcessorCount,(double)p.totalGlobalMem/(1ULL<<30));
    printf("[GPU %d] Range: %.3fT → %.3fT\n",
           dev,(double)base/1e12,(double)(base+total)/1e12);
    fflush(stdout);

    uint32_t *d_stop,*d_vcnt; uint16_t *d_vbuf;
    cudaMalloc(&d_stop,4);
    cudaMalloc(&d_vcnt,4);
    cudaMalloc(&d_vbuf, MAX_VALID*12*sizeof(uint16_t));

    /* Double-buffered pinned host memory: GPU fills A while CPU copies B */
    uint16_t* h_vbuf[2]; uint32_t* h_vcnt[2];
    for (int i=0;i<2;i++){
        cudaMallocHost(&h_vbuf[i], MAX_VALID*12*sizeof(uint16_t));
        cudaMallocHost(&h_vcnt[i], 4);
    }

    uint32_t zero=0;
    cudaMemcpy(d_stop,&zero,4,cudaMemcpyHostToDevice);

    const int BS=512;
    int cur=0; /* current pinned buffer index */
    uint64_t done=0;
    auto t0=std::chrono::high_resolution_clock::now();

    while (done<total && !G_found.load()){
        uint64_t batch=std::min(BATCH_SIZE, total-done);

        /* sync stop flag */
        uint32_t sf=G_found.load()?1u:0u;
        cudaMemcpy(d_stop,&sf,4,cudaMemcpyHostToDevice);
        cudaMemset(d_vcnt,0,4);

        int grid=(int)((batch+BS-1)/BS);
        dispersal_kernel<<<grid,BS>>>(base+done, batch, d_stop, d_vbuf, d_vcnt);
        cudaDeviceSynchronize();

        /* Copy results into current pinned buffer */
        cudaMemcpy(h_vcnt[cur],d_vcnt,4,cudaMemcpyDeviceToHost);
        uint32_t nv=*h_vcnt[cur];
        if (nv>MAX_VALID){ nv=MAX_VALID; } /* capped — batch sized to prevent this */

        if (nv>0)
            cudaMemcpy(h_vbuf[cur],d_vbuf,nv*12*sizeof(uint16_t),cudaMemcpyDeviceToHost);

        done+=batch;
        G_generated.fetch_add(batch);
        G_cs_pass.fetch_add(nv);

        /* Push valid candidates to queue (non-blocking for GPU) */
        if (nv>0)
            G_queue.push(h_vbuf[cur], nv);

        /* Flip buffer */
        cur^=1;

        /* ---- progress report every batch ---- */
        auto now=std::chrono::high_resolution_clock::now();
        double el    =std::chrono::duration<double>(now-t0).count();
        double el_tot=std::chrono::duration<double>(now-t_global_start).count();

        double gpu_spd   = (double)done/el/1e9;          /* this GPU G/s  */
        double pct_gpu   = (double)done/(double)total*100.0;
        double pct_total = (double)G_generated.load()/10740655718400.0*100.0;

        uint64_t rem_total = 10740655718400ULL - G_generated.load();
        double comb_spd  = (el_tot>0) ? (double)G_generated.load()/el_tot/1e9 : 0.0;
        double eta_s     = (comb_spd>0) ? (double)rem_total/(comb_spd*1e9) : 0.0;
        int eh=(int)(eta_s/3600), em=(int)(eta_s/60)%60, es2=(int)eta_s%60;

        printf("[GPU %d] %6.2f%% (this GPU) | Overall: %5.2f%% | "
               "Speed: %6.2f G/s | CS-pass: %llu | "
               "Queue: %zu | Verified: %llu | ETA: %02d:%02d:%02d\n",
               dev, pct_gpu, pct_total,
               gpu_spd,
               (unsigned long long)G_cs_pass.load(),
               G_queue.size(),
               (unsigned long long)G_verified.load(),
               eh, em, es2);
        fflush(stdout);
    }

    for (int i=0;i<2;i++){ cudaFreeHost(h_vbuf[i]); cudaFreeHost(h_vcnt[i]); }
    cudaFree(d_stop); cudaFree(d_vcnt); cudaFree(d_vbuf);
}

/* ============================================================
 * main
 * ============================================================ */
int main(int argc, char** argv){
    printf("============================================================\n");
    printf("  DUAL RTX 5090  --  FULL VERIFICATION DISPERSAL SOLVER\n");
    printf("  Target  : %s\n", TARGET_ADDR);
    printf("  Pipeline: GPU SHA-256 checksum → CPU thread-pool PBKDF2+BIP44\n");
    printf("  Fix     : Double-buffer + all CPU cores used (no GPU idle wait)\n");
    printf("============================================================\n");

    if (!load_wordlist()){
        fprintf(stderr,"ERROR: english.txt not found!\n"); return 1; }
    printf("BIP-39 wordlist loaded (2048 words)\n");

    int ndev=0; cudaGetDeviceCount(&ndev);
    printf("CUDA devices: %d\n",ndev);
    if (ndev<1){ fprintf(stderr,"No CUDA GPUs.\n"); return 1; }

    int ncpu = (int)std::thread::hardware_concurrency();
    if (ncpu<1) ncpu=4;
    printf("CPU cores for PBKDF2 verification: %d\n", ncpu);

    const uint64_t TOTAL=10740655718400ULL;
    int gpus=(ndev>=2)?2:1;
    uint64_t per=TOTAL/gpus;

    printf("Total combinations : %.2f Trillion\n", TOTAL/1e12);
    printf("GPUs               : %d  |  Batch per kernel: %.0fK\n",
           gpus, (double)BATCH_SIZE/1000.0);
    printf("MAX_VALID/batch    : %d  (overflow-safe for %.0fK * 7%%)\n\n",
           MAX_VALID, (double)BATCH_SIZE/1000.0);
    fflush(stdout);

    auto t_start=std::chrono::high_resolution_clock::now();

    /* Start CPU verifier thread pool */
    std::vector<std::thread> cpu_threads;
    for (int i=0;i<ncpu;i++)
        cpu_threads.emplace_back(cpu_verifier_thread);

    /* Start GPU worker threads */
    std::vector<std::thread> gpu_threads;
    for (int i=0;i<gpus;i++)
        gpu_threads.emplace_back(gpu_worker, i, (uint64_t)i*per, per, t_start);

    /* Combined summary every 60 seconds */
    std::thread summary([&](){
        while (!G_found.load()){
            std::this_thread::sleep_for(std::chrono::seconds(60));
            if (G_found.load()) break;
            auto now=std::chrono::high_resolution_clock::now();
            double el=std::chrono::duration<double>(now-t_start).count();
            uint64_t gen=G_generated.load();
            double pct=(double)gen/10740655718400.0*100.0;
            double spd=(double)gen/el/1e9;
            uint64_t rem=10740655718400ULL-gen;
            double eta_s=(spd>0)?(double)rem/(spd*1e9):0;
            int eh=(int)(eta_s/3600),em=(int)(eta_s/60)%60,es=(int)eta_s%60;
            printf("\n[SUMMARY] Overall: %.3f%% | %.3fT/10.74T | "
                   "Speed: %.2f G/s | CS-pass: %llu | "
                   "Verified: %llu | Queue: %zu | "
                   "Elapsed: %.0fs | ETA: %02d:%02d:%02d\n\n",
                   pct,(double)gen/1e12,spd,
                   (unsigned long long)G_cs_pass.load(),
                   (unsigned long long)G_verified.load(),
                   G_queue.size(),
                   el, eh,em,es);
            fflush(stdout);
        }
    });

    /* Wait for GPUs to finish */
    for (auto& t:gpu_threads) t.join();

    /* Signal CPU threads to drain queue then stop */
    G_queue.set_done();
    for (auto& t:cpu_threads) t.join();

    G_found.store(true); /* stop summary thread */
    summary.join();

    auto t_end=std::chrono::high_resolution_clock::now();
    double elapsed=std::chrono::duration<double>(t_end-t_start).count();

    printf("\n============================================================\n");
    printf("  SWEEP FINISHED\n");
    printf("  Generated      : %.3f Trillion\n",G_generated.load()/1e12);
    printf("  CS-pass        : %llu (%.3f%%)\n",
           (unsigned long long)G_cs_pass.load(),
           (G_generated.load()>0)?(double)G_cs_pass.load()/(double)G_generated.load()*100.0:0.0);
    printf("  Verified (CPU) : %llu\n",(unsigned long long)G_verified.load());
    printf("  Elapsed        : %.2f s  (%.2f min)\n",elapsed,elapsed/60.0);
    printf("  Combined speed : %.2f G/s\n",(double)G_generated.load()/elapsed/1e9);
    printf("  Result         : %s\n", G_found.load()?"FOUND!":"No match found.");
    printf("============================================================\n");

    return G_found.load()?0:1;
}


/* ============================================================
 * Standard includes
 * ============================================================ */
#include <cuda_runtime.h>
#include <device_launch_parameters.h>

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <atomic>
#include <chrono>
#include <thread>
#include <vector>

/* OpenSSL (host-side crypto) */
#include <openssl/evp.h>
#include <openssl/hmac.h>
#include <openssl/ripemd.h>
#include <openssl/sha.h>
/* secp256k1 via OpenSSL EC */
#include <openssl/bn.h>
#include <openssl/ec.h>
#include <openssl/obj_mac.h>

/* ============================================================
 * Target constants
 * ============================================================ */
static const char TARGET_ADDR[] = "1K4ezpLybootYF23TM4a8Y4NyP7auysnRo";
static const uint8_t TARGET_H160[20] = {
    0xc6,0x23,0x3a,0xeb,0x3a,0x50,0xa7,0x0b,
    0x82,0xfc,0xd8,0x8d,0x69,0xb5,0xf1,0xa3,
    0xec,0x6e,0x35,0x5a
};

/* ============================================================
 * 12-Block Dispersal data  (GPU constant memory)
 * ============================================================ */
__constant__ int      d_bsz[12]     = {10,7,7,13,8,8,4,10,12,7,12,13};
__constant__ uint16_t d_bwrd[12][16] = {
    {935,1004,646,545,532,1785,439,1754,1261,663},
    {58,1572,331,2038,1999,1785,1612},
    {1162,650,715,1302,532,1770,1785},
    {786,613,1004,1076,1500,2012,856,1832,517,650,2004,786,1600},
    {856,1891,1785,786,1406,664,331,201},
    {396,786,1785,160,1863,67,1548,331},
    {1284,287,2004,1898},
    {1302,1234,1261,1032,735,2010,102,1265,1754,102},
    {1265,650,786,856,1162,1762,1222,1195,2046,1785,1698,786},
    {160,935,1194,829,1904,1605,1234},
    {191,786,401,0,863,646,400,1605,1028,1861,1234,35},
    {1899,863,1193,1162,35,1374,431,1770,1710,1698,1787,1221,843}
};

/* ============================================================
 * Device SHA-256  (single 16-byte input → first output byte)
 * We only need the first byte of SHA-256(entropy[16]) to get
 * the 4-bit checksum for a 12-word BIP-39 mnemonic.
 * ============================================================ */
#define ROTR(x,n) (((x)>>(n))|((x)<<(32-(n))))
#define SHR(x,n)  ((x)>>(n))
#define CH(x,y,z) (((x)&(y))^(~(x)&(z)))
#define MAJ(x,y,z)(((x)&(y))^((x)&(z))^((y)&(z)))
#define EP0(x) (ROTR(x,2)^ROTR(x,13)^ROTR(x,22))
#define EP1(x) (ROTR(x,6)^ROTR(x,11)^ROTR(x,25))
#define SG0(x) (ROTR(x,7)^ROTR(x,18)^SHR(x,3))
#define SG1(x) (ROTR(x,17)^ROTR(x,19)^SHR(x,10))

__device__ __constant__ uint32_t K256[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,
    0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,
    0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,
    0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,
    0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,
    0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,
    0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,
    0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,
    0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};

/* SHA-256 of exactly 16 bytes; returns only the first output byte */
__device__ __forceinline__ uint8_t sha256_16b_firstbyte(const uint8_t* d) {
    uint32_t h0=0x6a09e667, h1=0xbb67ae85, h2=0x3c6ef372, h3=0xa54ff53a;
    uint32_t h4=0x510e527f, h5=0x9b05688c, h6=0x1f83d9ab, h7=0x5be0cd19;

    uint32_t W[64];
    /* load 16 bytes as 4 big-endian words */
    for (int i=0;i<4;i++)
        W[i] = ((uint32_t)d[i*4]<<24)|((uint32_t)d[i*4+1]<<16)|
               ((uint32_t)d[i*4+2]<<8)|(uint32_t)d[i*4+3];
    W[4]=0x80000000;
    for (int i=5;i<15;i++) W[i]=0;
    W[15]=0x00000080; /* length = 128 bits */

    for (int i=16;i<64;i++)
        W[i]=SG1(W[i-2])+W[i-7]+SG0(W[i-15])+W[i-16];

    uint32_t a=h0,b=h1,c=h2,d2=h3,e=h4,f=h5,g=h6,hh=h7;
    for (int i=0;i<64;i++){
        uint32_t T1=hh+EP1(e)+CH(e,f,g)+K256[i]+W[i];
        uint32_t T2=EP0(a)+MAJ(a,b,c);
        hh=g; g=f; f=e; e=d2+T1;
        d2=c; c=b; b=a; a=T1+T2;
    }
    return (uint8_t)((h0+a)>>24);
}

/* Real BIP-39 checksum for 12 words */
__device__ __forceinline__ int real_bip39_check(const uint16_t* idx) {
    uint8_t bits[17]={0};
    int bp=0;
    for (int i=0;i<12;i++){
        uint16_t v=idx[i];
        for (int b=10;b>=0;b--){
            uint8_t bit=(v>>b)&1;
            bits[bp/8]|=(bit<<(7-(bp%8)));
            bp++;
        }
    }
    uint8_t expected=(bits[16]>>4)&0x0F;
    uint8_t actual  =(sha256_16b_firstbyte(bits)>>4)&0x0F;
    return (expected==actual)?1:0;
}

/* ============================================================
 * GPU kernel: generate + filter, store valid into output buffer
 * ============================================================ */
#define MAX_VALID 32768  /* per batch; sized for pinned memory */

__global__ void dispersal_kernel(
    uint64_t base_id,
    uint64_t count,
    volatile uint32_t* __restrict__ g_stop,     /* set to 1 when answer found */
    uint16_t*          __restrict__ g_valid_buf, /* [MAX_VALID * 12] */
    volatile uint32_t* __restrict__ g_valid_cnt
){
    uint64_t tid = (uint64_t)blockDim.x*blockIdx.x + threadIdx.x;
    if (tid>=count || *g_stop) return;

    uint64_t id=base_id+tid;
    uint16_t cand[12];
    uint64_t rem=id;
    for (int b=11;b>=0;b--){
        int sz=d_bsz[b];
        cand[b]=d_bwrd[b][rem%sz];
        rem/=sz;
    }

    if (real_bip39_check(cand)){
        uint32_t slot=atomicAdd((uint32_t*)g_valid_cnt,1u);
        if (slot<MAX_VALID){
            uint16_t* dst=g_valid_buf+slot*12;
            for (int i=0;i<12;i++) dst[i]=cand[i];
        }
    }
}

/* ============================================================
 * Host-side BIP-39 → seed → BIP-32/BIP-44 → Hash160 verification
 * Uses OpenSSL throughout (available on every CUDA dev server)
 * ============================================================ */
static const char* WL[2048];   /* wordlist */
static bool wl_ok=false;

static bool load_wordlist(){
    const char* paths[]={"../../english.txt","../english.txt","english.txt",nullptr};
    for (int pi=0;paths[pi];pi++){
        FILE* f=fopen(paths[pi],"r");
        if (!f) continue;
        char buf[64]; int n=0;
        while (n<2048 && fgets(buf,sizeof(buf),f)){
            int L=strlen(buf);
            while (L>0&&(buf[L-1]=='\n'||buf[L-1]=='\r')) buf[--L]=0;
            WL[n++]=strdup(buf);
        }
        fclose(f);
        if (n==2048){ wl_ok=true; return true; }
    }
    return false;
}

static void indices_to_phrase(const uint16_t* idx, char* out, size_t cap){
    out[0]=0;
    for (int i=0;i<12;i++){
        if (i) strncat(out," ",cap-1);
        strncat(out,WL[idx[i]],cap-1);
    }
}

/* PBKDF2-HMAC-SHA512 → 64-byte BIP-39 seed */
static void phrase_to_seed(const char* phrase, uint8_t seed[64]){
    const char salt[]="mnemonic"; /* no extra passphrase */
    PKCS5_PBKDF2_HMAC(phrase,(int)strlen(phrase),
                      (const uint8_t*)salt,(int)strlen(salt),
                      2048,EVP_sha512(),64,seed);
}

/* HMAC-SHA512 wrapper */
static void hmac512(const uint8_t* key,int klen,
                    const uint8_t* data,int dlen,
                    uint8_t out[64]){
    unsigned int olen=64;
    HMAC(EVP_sha512(),key,klen,data,dlen,out,&olen);
}

/* secp256k1 order n */
static const uint8_t N32[32]={
    0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,
    0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xfe,
    0xba,0xae,0xdc,0xe6,0xaf,0x48,0xa0,0x3b,
    0xbf,0xd2,0x5e,0x8c,0xd0,0x36,0x41,0x41
};

struct XKey { uint8_t prv[32], chn[32]; };

/* BIP-32 master key from 64-byte seed */
static XKey master_from_seed(const uint8_t* seed){
    XKey k;
    uint8_t I[64];
    hmac512((uint8_t*)"Bitcoin seed",12,seed,64,I);
    memcpy(k.prv,I,32);
    memcpy(k.chn,I+32,32);
    return k;
}

/* compressed public key (33 bytes) from private key */
static bool pubkey33(const uint8_t* prv32, uint8_t* pub33){
    EC_GROUP* G=EC_GROUP_new_by_curve_name(NID_secp256k1);
    if (!G) return false;
    BIGNUM* bn=BN_bin2bn(prv32,32,NULL);
    EC_POINT* P=EC_POINT_new(G);
    EC_POINT_mul(G,P,bn,NULL,NULL,NULL);
    BN_CTX* ctx=BN_CTX_new();
    size_t len=EC_POINT_point2oct(G,P,POINT_CONVERSION_COMPRESSED,pub33,33,ctx);
    BN_free(bn); EC_POINT_free(P); EC_GROUP_free(G); BN_CTX_free(ctx);
    return len==33;
}

/* Hash160 = RIPEMD160(SHA256(data)) */
static void hash160(const uint8_t* data, int dlen, uint8_t h160[20]){
    uint8_t sha[32];
    SHA256(data,dlen,sha);
    RIPEMD160(sha,32,h160);
}

/* BIP-32 child key derivation */
static bool child(const XKey& par, uint32_t idx, bool hard, XKey& out){
    uint8_t data[37];
    uint32_t i32=hard?(idx|0x80000000u):idx;
    if (hard){
        data[0]=0x00;
        memcpy(data+1,par.prv,32);
    } else {
        uint8_t pub[33];
        if (!pubkey33(par.prv,pub)) return false;
        memcpy(data,pub,33);
    }
    data[33]=(i32>>24)&0xFF; data[34]=(i32>>16)&0xFF;
    data[35]=(i32>>8)&0xFF;  data[36]=i32&0xFF;

    uint8_t I[64];
    hmac512(par.chn,32,data,37,I);

    BIGNUM* il=BN_bin2bn(I,32,NULL);
    BIGNUM* pk=BN_bin2bn(par.prv,32,NULL);
    BIGNUM* n =BN_bin2bn(N32,32,NULL);
    BIGNUM* ck=BN_new();
    BN_CTX* ctx=BN_CTX_new();
    BN_mod_add(ck,il,pk,n,ctx);
    bool ok=!BN_is_zero(ck);
    BN_bn2binpad(ck,out.prv,32);
    memcpy(out.chn,I+32,32);
    BN_free(il); BN_free(pk); BN_free(n); BN_free(ck); BN_CTX_free(ctx);
    return ok;
}

/* Try one candidate: returns true + fills phrase/path if match */
static bool verify_candidate(const uint16_t* indices, char* phrase_out, char* path_out){
    if (!wl_ok) return false;

    char phrase[256]; indices_to_phrase(indices,phrase,sizeof(phrase));
    uint8_t seed[64]; phrase_to_seed(phrase,seed);
    XKey M=master_from_seed(seed);

    /* ---- check root key ---- */
    {
        uint8_t pub[33]; uint8_t h160[20];
        if (pubkey33(M.prv,pub)){ hash160(pub,33,h160);
            if (!memcmp(h160,TARGET_H160,20)){
                strcpy(phrase_out,phrase); strcpy(path_out,"m"); return true; } }
    }

    /* ---- BIP-44  m/44'/0'/0'/0/i ---- */
    {
        XKey a,b,c2,ext;
        if (child(M,44,true,a) && child(a,0,true,b) &&
            child(b,0,true,c2)&& child(c2,0,false,ext)){
            for (uint32_t i=0;i<10;i++){
                XKey leaf; if (!child(ext,i,false,leaf)) continue;
                uint8_t pub[33]; uint8_t h160[20];
                if (pubkey33(leaf.prv,pub)){ hash160(pub,33,h160);
                    if (!memcmp(h160,TARGET_H160,20)){
                        strcpy(phrase_out,phrase);
                        sprintf(path_out,"m/44'/0'/0'/0/%u",i); return true; } }
            }
        }
        /* change chain m/44'/0'/0'/1/i */
        if (child(M,44,true,a)&&child(a,0,true,b)&&
            child(b,0,true,c2)&&child(c2,1,false,ext)){
            for (uint32_t i=0;i<5;i++){
                XKey leaf; if (!child(ext,i,false,leaf)) continue;
                uint8_t pub[33]; uint8_t h160[20];
                if (pubkey33(leaf.prv,pub)){ hash160(pub,33,h160);
                    if (!memcmp(h160,TARGET_H160,20)){
                        strcpy(phrase_out,phrase);
                        sprintf(path_out,"m/44'/0'/0'/1/%u",i); return true; } }
            }
        }
    }

    /* ---- m/0/i  (Electrum-style) ---- */
    {
        XKey m0;
        if (child(M,0,false,m0)){
            for (uint32_t i=0;i<5;i++){
                XKey leaf; if (!child(m0,i,false,leaf)) continue;
                uint8_t pub[33]; uint8_t h160[20];
                if (pubkey33(leaf.prv,pub)){ hash160(pub,33,h160);
                    if (!memcmp(h160,TARGET_H160,20)){
                        strcpy(phrase_out,phrase);
                        sprintf(path_out,"m/0/%u",i); return true; } }
            }
        }
    }

    return false;
}

/* ============================================================
 * Shared progress counters
 * ============================================================ */
static std::atomic<uint64_t> G_generated(0);
static std::atomic<uint64_t> G_cs_pass(0);
static std::atomic<bool>     G_found(false);

/* ============================================================
 * Per-GPU worker thread
 * ============================================================ */
static void gpu_worker(int dev, uint64_t base, uint64_t total){
    cudaSetDevice(dev);
    cudaDeviceProp p; cudaGetDeviceProperties(&p,dev);
    printf("[GPU %d] %s  SMs=%d  VRAM=%.1fGB\n",
           dev,p.name,p.multiProcessorCount,
           (double)p.totalGlobalMem/(1ULL<<30));
    printf("[GPU %d] Assigned range: %.3fT - %.3fT  (%.3f Trillion total)\n",
           dev, (double)base/1e12, (double)(base+total)/1e12, (double)total/1e12);
    fflush(stdout);

    /* GPU buffers */
    uint32_t *d_stop, *d_vcnt;
    uint16_t *d_vbuf;
    cudaMalloc(&d_stop,sizeof(uint32_t));
    cudaMalloc(&d_vcnt,sizeof(uint32_t));
    cudaMalloc(&d_vbuf, MAX_VALID*12*sizeof(uint16_t));

    /* Pinned host buffers */
    uint16_t* h_vbuf; uint32_t* h_vcnt;
    cudaMallocHost(&h_vbuf, MAX_VALID*12*sizeof(uint16_t));
    cudaMallocHost(&h_vcnt, sizeof(uint32_t));

    uint32_t zero=0;
    cudaMemcpy(d_stop,&zero,4,cudaMemcpyHostToDevice);

    const uint64_t BATCH = 100000000ULL; /* 100M per launch */
    const int BS=512;
    uint64_t done=0;
    auto t0=std::chrono::high_resolution_clock::now();

    while (done<total && !G_found.load()){
        uint64_t cur=std::min(BATCH, total-done);

        /* sync stop flag */
        uint32_t sf=G_found.load()?1u:0u;
        cudaMemcpy(d_stop,&sf,4,cudaMemcpyHostToDevice);

        cudaMemset(d_vcnt,0,4);

        int grid=(int)((cur+BS-1)/BS);
        dispersal_kernel<<<grid,BS>>>(
            base+done, cur, d_stop, d_vbuf, d_vcnt);
        cudaDeviceSynchronize();

        cudaMemcpy(h_vcnt,d_vcnt,4,cudaMemcpyDeviceToHost);
        uint32_t nv=*h_vcnt;
        if (nv>MAX_VALID) nv=MAX_VALID;

        done+=cur;
        G_generated.fetch_add(cur);
        G_cs_pass.fetch_add(nv);

        if (nv>0){
            cudaMemcpy(h_vbuf,d_vbuf,nv*12*sizeof(uint16_t),cudaMemcpyDeviceToHost);
            for (uint32_t i=0;i<nv&&!G_found.load();i++){
                char phrase[256]="", path[64]="";
                if (verify_candidate(h_vbuf+i*12, phrase, path)){
                    G_found.store(true);
                    printf("\n");
                    printf("============================================================\n");
                    printf("  TARGET FOUND  (GPU %d verified)\n", dev);
                    printf("  Mnemonic : %s\n", phrase);
                    printf("  Path     : %s\n", path);
                    printf("  Address  : %s\n", TARGET_ADDR);
                    printf("============================================================\n");
                    fflush(stdout);
                }
            }
        }

        /* ---- progress report ---- */
        auto now=std::chrono::high_resolution_clock::now();
        double el=std::chrono::duration<double>(now-t0).count();

        /* per-GPU speed (candidates/s this GPU only) */
        double gpu_speed = (double)done / el / 1e9;   /* G/s */

        /* combined throughput across all GPUs */
        double comb_speed = (double)G_generated.load() / el / 1e9;

        /* progress % for this GPU's slice */
        double pct = (total > 0) ? (double)done / (double)total * 100.0 : 0.0;

        /* overall progress % across all GPUs */
        double pct_total = (double)G_generated.load() / 10740655718400.0 * 100.0;

        /* ETA in seconds (based on combined speed for remaining total work) */
        uint64_t remaining = 10740655718400ULL - G_generated.load();
        double eta_s = (comb_speed > 0.0)
                       ? (double)remaining / (comb_speed * 1e9)
                       : 0.0;

        /* format ETA as hh:mm:ss */
        int eta_h  = (int)(eta_s / 3600);
        int eta_m  = (int)(eta_s / 60) % 60;
        int eta_s2 = (int)eta_s % 60;

        printf("[GPU %d] Progress: %.2f%%  (this GPU: %.3fT/5.37T)  "
               "Overall: %.2f%%  "
               "Speed: %.2f G/s  "
               "CS-pass: %llu  "
               "ETA: %02d:%02d:%02d\n",
               dev,
               pct,
               (double)done / 1e12,
               pct_total,
               gpu_speed,
               (unsigned long long)G_cs_pass.load(),
               eta_h, eta_m, eta_s2);
        fflush(stdout);
    }

    cudaFreeHost(h_vbuf); cudaFreeHost(h_vcnt);
    cudaFree(d_stop); cudaFree(d_vcnt); cudaFree(d_vbuf);
}

/* ============================================================
 * main
 * ============================================================ */
int main(int argc, char** argv){
    printf("============================================================\n");
    printf("  DUAL RTX 5090  --  FULL VERIFICATION DISPERSAL SOLVER\n");
    printf("  Target  : %s\n", TARGET_ADDR);
    printf("  Pipeline: GPU SHA-256 checksum filter\n");
    printf("            + CPU PBKDF2-HMAC-SHA512 + BIP-32/44 + Hash160\n");
    printf("============================================================\n");

    if (!load_wordlist()){
        fprintf(stderr,"ERROR: english.txt wordlist not found!\n"); return 1; }
    printf("BIP-39 wordlist loaded (2048 words)\n");

    int ndev=0;
    cudaGetDeviceCount(&ndev);
    printf("CUDA devices detected: %d\n",ndev);
    if (ndev<1){ fprintf(stderr,"No CUDA GPUs.\n"); return 1; }

    const uint64_t TOTAL=10740655718400ULL;
    int gpus=(ndev>=2)?2:1;
    uint64_t per=(TOTAL/gpus);

    printf("Total combinations : %.2f Trillion\n",TOTAL/1e12);
    printf("GPUs in use        : %d\n",gpus);
    printf("Work per GPU       : %.2f Trillion\n\n",per/1e12);
    fflush(stdout);

    auto t_start=std::chrono::high_resolution_clock::now();
    std::vector<std::thread> threads;
    for (int i=0;i<gpus;i++)
        threads.emplace_back(gpu_worker, i, (uint64_t)i*per, per);

    /* ---- combined summary thread (prints every 30s) ---- */
    std::thread summary_thread([&](){
        const uint64_t TOTAL_CMB=10740655718400ULL;
        while (!G_found.load()){
            std::this_thread::sleep_for(std::chrono::seconds(30));
            if (G_found.load()) break;
            auto now=std::chrono::high_resolution_clock::now();
            double el=std::chrono::duration<double>(now-t_start).count();
            uint64_t gen=G_generated.load();
            uint64_t csp=G_cs_pass.load();
            double pct=(double)gen/(double)TOTAL_CMB*100.0;
            double speed=(double)gen/el/1e9;
            uint64_t rem=TOTAL_CMB-gen;
            double eta_s=(speed>0)?(double)rem/(speed*1e9):0;
            int eh=(int)(eta_s/3600), em=(int)(eta_s/60)%60, es=(int)eta_s%60;
            printf("\n[COMBINED] Overall: %.2f%% | %.3fT / 10.74T | "
                   "Speed: %.2f G/s | CS-pass: %llu | "
                   "Elapsed: %.0fs | ETA: %02d:%02d:%02d\n\n",
                   pct, (double)gen/1e12, speed,
                   (unsigned long long)csp,
                   el, eh, em, es);
            fflush(stdout);
        }
    });

    for (auto& t:threads) t.join();
    G_found.store(true);   /* signal summary thread to stop */
    summary_thread.join();

    auto t_end=std::chrono::high_resolution_clock::now();
    double elapsed=std::chrono::duration<double>(t_end-t_start).count();

    printf("\n============================================================\n");
    printf("  SWEEP FINISHED\n");
    printf("  Generated      : %.2f Trillion\n",G_generated.load()/1e12);
    printf("  Checksum pass  : %llu (%.3f%%)\n",
           (unsigned long long)G_cs_pass.load(),
           (double)G_cs_pass.load()/(double)G_generated.load()*100.0);
    printf("  Elapsed        : %.2f s  (%.2f min)\n",elapsed,elapsed/60.0);
    printf("  Result         : %s\n", G_found.load()?"FOUND!":"No match found.");
    printf("============================================================\n");

    return G_found.load()?0:1;
}
