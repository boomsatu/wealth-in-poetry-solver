use crate::bip39::word_index;

pub const REVOLUTION_PARAGRAPHS: &[&str] = &[
    "My grandfather, known to me as ‘ye-ye’, was born into a large well-to-do merchant class family in the early 1930’s during a troubled time in China. A decade after the dissolution of dynastic imperialism that lasted over 2000 years, China in the 1920’s was fighting to find its identity among a massive cultural shift, warlordism, and civil war in an increasingly global world.",
    "Tensions were brewing while my ye-ye grew up in what he describes as an idyllic childhood despite unsettling clues of a quietly turbulent and changing time. He was the eldest of six siblings born to a mother of bound feet and a successful merchant father who would disappear most afternoons to frequent opium dens, or as he called them, ‘tea’ houses.",
    "Thousands of years of changing dynastic rules ingrained cautions of inflationary currency in Chinese psyche and most people during this time turned to gold as savings as well as an informal medium of exchange. My ye-ye remembers a large wooden cabinet in the main sitting room of his house where a hidden trap door was installed by his father. In it held the majority of his family’s wealth in gold and silver — the rest was hidden in the ground under his mother’s wooden wardrobe.",
    "(At the time of my ye-ye’s childhood, a ‘tael’ of gold could purchase 40 bags of fine flour at 40 lbs each — towards the peak of civil unrest, a passage on boat from the mainland to Taiwan could cost up to 10 taels of gold.)",
    "By the time my ye-ye turned eighteen, the Japanese were retreating and the temporary truce between two clashing political ideals was falling apart. The Second Japo-Sino war impoverished both sides — while the Kuomintang (KMT) increased inflation to pay its debts from civil war funding, the Communist Party of China (CPC) was being energized by the masses of peasants looking for a revolution.",
    "Driving the rhetoric of the communist cause was the underlying distrust and bitterness of wealth held by the upper classes for centuries and the promise from the CPC to redistribute lands to the people once the war was over. Lands owned by families like my ye-ye’s.",
    "Whatever future he had envisioned for himself disappeared when it became too dangerous to assume his own identity. It was decided that he and his siblings would disband and assume new identities for their own safety. His father removed five taels of gold from his hidden cabinet and his mother hid them in my ye-ye’s clothes and shoes. They sent him off to Qingdao — a relatively neutral zone at the time. He still remembers the feeling of the gold yuanbao wedged in between his toes and the lump he felt on his underarm from being sewn into the lining of his shirt.",
    "Once he arrived in Qingdao and situations seemed bleak, my ye-ye gave his five gold yuanbao meant for his survival to his cousin and decided he was going to abandon his home, his family, his country. He has since rebuilt his life twice, once as a refugee in Taiwan and again as an immigrant in Canada. It would be 50 years until he returned to his ancestral home — he never saw his mother again.",
    "From China to Zimbabwe to present day Venezuela, this worst-case scenario isn’t an exceptional story — economic and political refugees are still fleeing oppressive regimes today often with heavy financial costs in exchange for freedom."
];

pub fn get_revolution_words() -> Vec<String> {
    let mut words = Vec::new();
    for p in REVOLUTION_PARAGRAPHS {
        for w in p.split_whitespace() {
            let clean: String = w.chars().filter(|c| c.is_alphabetic()).flat_map(|c| c.to_lowercase()).collect();
            if !clean.is_empty() {
                words.push(clean);
            }
        }
    }
    words
}

pub fn get_revolution_bip39_occurrences() -> Vec<(usize, u16, String)> {
    let words = get_revolution_words();
    let mut occ = Vec::new();
    for (i, w) in words.iter().enumerate() {
        if let Some(idx) = word_index(w) {
            occ.push((i, idx, w.clone()));
        }
    }
    occ
}

#[allow(dead_code)]
pub fn get_revolution_unique_bip39() -> Vec<(u16, String)> {
    let occ = get_revolution_bip39_occurrences();
    let mut unique = Vec::new();
    let mut seen = std::collections::HashSet::new();
    for (_, idx, w) in occ {
        if seen.insert(idx) {
            unique.push((idx, w));
        }
    }
    unique
}

/// 12 Dispersal Blocks from the Revolution story (chronological 12-section partition)
pub const DISPERSAL_12_BLOCKS: [&[u16]; 12] = [
    // Block 0: into(935), large(1004), family(646), early(545), during(532), time(1785), decade(439), that(1754), over(1261), find(663)
    &[935, 1004, 646, 545, 532, 1785, 439, 1754, 1261, 663],
    // Block 1: among(58), shift(1572), civil(331), world(2038), what(1999), time(1785), six(1612)
    &[58, 1572, 331, 2038, 1999, 1785, 1612],
    // Block 2: mother(1162), father(650), frequent(715), people(1302), during(532), this(1770), time(1785)
    &[1162, 650, 715, 1302, 532, 1770, 1785],
    // Block 3: gold(786), exchange(613), large(1004), main(1076), room(1500), where(2012), hidden(856), trap(1832), door(517), father(650), wealth(2004), gold(786), silver(1600)
    &[786, 613, 1004, 1076, 1500, 2012, 856, 1832, 517, 650, 2004, 786, 1600],
    // Block 4: hidden(856), under(1891), time(1785), gold(786), purchase(1406), fine(664), civil(331), boat(201)
    &[856, 1891, 1785, 786, 1406, 664, 331, 201],
    // Block 5: cost(396), gold(786), time(1785), between(160), two(1863), apart(67), second(1548), civil(331)
    &[396, 786, 1785, 160, 1863, 67, 1548, 331],
    // Block 6: party(1284), cause(287), wealth(2004), upper(1898)
    &[1284, 287, 2004, 1898],
    // Block 7: people(1302), once(1234), over(1261), like(1032), future(735), when(2010), assume(102), own(1265), that(1754), assume(102)
    &[1302, 1234, 1261, 1032, 735, 2010, 102, 1265, 1754, 102],
    // Block 8: own(1265), father(650), gold(786), hidden(856), mother(1162), they(1762), off(1222), neutral(1195), zone(2046), time(1785), still(1698), gold(786)
    &[1265, 650, 786, 856, 1162, 1762, 1222, 1195, 2046, 1785, 1698, 786],
    // Block 9: between(160), into(935), network(1194), have(829), used(1904), since(1605), once(1234)
    &[160, 935, 1194, 829, 1904, 1605, 1234],
    // Block 10: bleak(191), gold(786), cousin(401), abandon(0), home(863), family(646), country(400), since(1605), life(1028), twice(1861), once(1234), again(35)
    &[191, 786, 401, 0, 863, 646, 400, 1605, 1028, 1861, 1234, 35],
    // Block 11: until(1899), home(863), never(1193), mother(1162), again(35), present(1374), day(431), this(1770), story(1710), still(1698), today(1787), often(1221), heavy(843)
    &[1899, 863, 1193, 1162, 35, 1374, 431, 1770, 1710, 1698, 1787, 1221, 843],
];
