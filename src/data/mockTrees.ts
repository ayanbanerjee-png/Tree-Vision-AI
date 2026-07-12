import { TreeAnalysis, DashboardStats } from '../types';

export const INITIAL_MOCK_TREES: TreeAnalysis[] = [
  {
    id: 'TR-1082',
    species: 'Neem (Azadirachta indica)',
    confidence: 94,
    speciesGroup: 'Broadleaf Evergreen',
    health: 'Healthy',
    age: 'Young',
    foliage: 'Full Canopy',
    imageQuality: 'Clear',
    occlusion: 'No',
    needsReview: false,
    timestamp: '2026-07-09T08:30:00Z',
    top5: [
      { species: 'Neem (Azadirachta indica)', confidence: 94 },
      { species: 'Chinaberry (Melia azedarach)', confidence: 4 },
      { species: 'Curry Leaf Tree (Murraya koenigii)', confidence: 1 },
      { species: 'Mahogany (Swietenia mahagoni)', confidence: 0.7 },
      { species: 'Ash Tree (Fraxinus)', confidence: 0.3 }
    ]
  },
  {
    id: 'TR-1081',
    species: 'Banyan (Ficus benghalensis)',
    confidence: 88,
    speciesGroup: 'Ficus',
    health: 'Healthy',
    age: 'Ancient',
    foliage: 'Full Canopy',
    imageQuality: 'Clear',
    occlusion: 'Partial',
    needsReview: false,
    timestamp: '2026-07-09T06:15:00Z',
    top5: [
      { species: 'Banyan (Ficus benghalensis)', confidence: 88 },
      { species: 'Peepal (Ficus religiosa)', confidence: 9 },
      { species: 'Rubber Tree (Ficus elastica)', confidence: 2 },
      { species: 'Cluster Fig (Ficus racemosa)', confidence: 0.8 },
      { species: 'Weeping Fig (Ficus benjamina)', confidence: 0.2 }
    ]
  },
  {
    id: 'TR-1080',
    species: 'Mango Tree (Mangifera indica)',
    confidence: 62,
    speciesGroup: 'Fruit Tree',
    health: 'Mild Decline',
    age: 'Mature',
    foliage: 'Moderate',
    imageQuality: 'Low Light',
    occlusion: 'Heavy',
    needsReview: true,
    timestamp: '2026-07-08T18:45:00Z',
    top5: [
      { species: 'Mango Tree (Mangifera indica)', confidence: 62 },
      { species: 'Cashew Tree (Anacardium occidentale)', confidence: 21 },
      { species: 'Jackfruit Tree (Artocarpus heterophyllus)', confidence: 11 },
      { species: 'Guava Tree (Psidium guajava)', confidence: 4 },
      { species: 'Sapodilla (Manilkara zapota)', confidence: 2 }
    ]
  },
  {
    id: 'TR-1079',
    species: 'Eucalyptus (Eucalyptus globulus)',
    confidence: 97,
    speciesGroup: 'Myrtaceae',
    health: 'Healthy',
    age: 'Semi-Mature',
    foliage: 'Full Canopy',
    imageQuality: 'Clear',
    occlusion: 'No',
    needsReview: false,
    timestamp: '2026-07-08T14:20:00Z',
    top5: [
      { species: 'Eucalyptus (Eucalyptus globulus)', confidence: 97 },
      { species: 'Paperbark (Melaleuca quinquenervia)', confidence: 1.5 },
      { species: 'Red Gum (Eucalyptus camaldulensis)', confidence: 1.0 },
      { species: 'Silver Wattle (Acacia dealbata)', confidence: 0.4 },
      { species: 'Corymbia (Corymbia maculata)', confidence: 0.1 }
    ]
  },
  {
    id: 'TR-1078',
    species: 'Peepal (Ficus religiosa)',
    confidence: 45,
    speciesGroup: 'Ficus',
    health: 'Severe Disease',
    age: 'Mature',
    foliage: 'Sparse',
    imageQuality: 'Blurry',
    occlusion: 'Partial',
    needsReview: true,
    timestamp: '2026-07-08T11:05:00Z',
    top5: [
      { species: 'Peepal (Ficus religiosa)', confidence: 45 },
      { species: 'Banyan (Ficus benghalensis)', confidence: 38 },
      { species: 'Sacred Fig (Ficus rumphii)', confidence: 12 },
      { species: 'Bodhi Tree (Ficus)', confidence: 4 },
      { species: 'Mulberry (Morus alba)', confidence: 1 }
    ]
  },
  {
    id: 'TR-1077',
    species: 'Coconut Palm (Cocos nucifera)',
    confidence: 99,
    speciesGroup: 'Palm',
    health: 'Healthy',
    age: 'Mature',
    foliage: 'Full Canopy',
    imageQuality: 'Clear',
    occlusion: 'No',
    needsReview: false,
    timestamp: '2026-07-07T16:50:00Z',
    top5: [
      { species: 'Coconut Palm (Cocos nucifera)', confidence: 99 },
      { species: 'Areca Palm (Dypsis lutescens)', confidence: 0.8 },
      { species: 'Date Palm (Phoenix dactylifera)', confidence: 0.1 },
      { species: 'Oil Palm (Elaeis guineensis)', confidence: 0.08 },
      { species: 'Fan Palm (Washingtonia)', confidence: 0.02 }
    ]
  },
  {
    id: 'TR-1076',
    species: 'Teak (Tectona grandis)',
    confidence: 84,
    speciesGroup: 'Lamiaceae',
    health: 'Mild Decline',
    age: 'Semi-Mature',
    foliage: 'Moderate',
    imageQuality: 'Clear',
    occlusion: 'No',
    needsReview: false,
    timestamp: '2026-07-07T09:30:00Z',
    top5: [
      { species: 'Teak (Tectona grandis)', confidence: 84 },
      { species: 'Sal Tree (Shorea robusta)', confidence: 9 },
      { species: 'Rosewood (Dalbergia sissoo)', confidence: 4 },
      { species: 'Mahogany (Swietenia macrophylla)', confidence: 2 },
      { species: 'Sandalwood (Santalum album)', confidence: 1 }
    ]
  }
];

export const getStats = (trees: TreeAnalysis[]): DashboardStats => {
  const total = trees.length;
  const avgConf = trees.reduce((acc, t) => acc + t.confidence, 0) / (total || 1);
  const needsReview = trees.filter(t => t.needsReview).length;
  const healthy = trees.filter(t => t.health === 'Healthy').length;

  return {
    imagesProcessed: total,
    avgConfidence: Math.round(avgConf),
    needsReviewCount: needsReview,
    healthyTreesCount: healthy
  };
};

const SPECIES_TEMPLATES = [
  { name: 'Neem (Azadirachta indica)', group: 'Broadleaf Evergreen' },
  { name: 'Banyan (Ficus benghalensis)', group: 'Ficus' },
  { name: 'Mango Tree (Mangifera indica)', group: 'Fruit Tree' },
  { name: 'Eucalyptus (Eucalyptus globulus)', group: 'Myrtaceae' },
  { name: 'Peepal (Ficus religiosa)', group: 'Ficus' },
  { name: 'Coconut Palm (Cocos nucifera)', group: 'Palm' },
  { name: 'Teak (Tectona grandis)', group: 'Lamiaceae' }
];

export const generateMockAnalysis = (fileName: string): TreeAnalysis => {
  const randomId = `TR-${Math.floor(1000 + Math.random() * 9000)}`;
  const templateIndex = Math.floor(Math.random() * SPECIES_TEMPLATES.length);
  const selectedTemplate = SPECIES_TEMPLATES[templateIndex];
  
  const confidence = Math.floor(40 + Math.random() * 59); // 40% - 99%
  const needsReview = confidence < 75 || Math.random() > 0.85;

  const healths: ('Healthy' | 'Mild Decline' | 'Severe Disease')[] = ['Healthy', 'Mild Decline', 'Severe Disease'];
  const healthWeight = Math.random();
  const health = healthWeight > 0.7 ? (healthWeight > 0.9 ? healths[2] : healths[1]) : healths[0];

  const ages: ('Young' | 'Semi-Mature' | 'Mature' | 'Ancient')[] = ['Young', 'Semi-Mature', 'Mature', 'Ancient'];
  const age = ages[Math.floor(Math.random() * ages.length)];

  const foliages: ('Full Canopy' | 'Moderate' | 'Sparse' | 'None')[] = ['Full Canopy', 'Moderate', 'Sparse', 'None'];
  const foliage = foliages[Math.floor(Math.random() * foliages.length)];

  const qualities: ('Clear' | 'Blurry' | 'Low Light')[] = ['Clear', 'Blurry', 'Low Light'];
  const imageQuality = confidence > 80 ? qualities[0] : qualities[Math.floor(Math.random() * qualities.length)];

  const occlusions: ('No' | 'Partial' | 'Heavy')[] = ['No', 'Partial', 'Heavy'];
  const occlusion = occlusions[Math.floor(Math.random() * occlusions.length)];

  // Generate top-5 predictions
  const baseConf = confidence;
  const remainingConf = 100 - baseConf;
  const conf1 = Math.floor(remainingConf * 0.6);
  const conf2 = Math.floor(remainingConf * 0.25);
  const conf3 = Math.floor(remainingConf * 0.1);
  const conf4 = remainingConf - conf1 - conf2 - conf3;

  const otherTemplates = SPECIES_TEMPLATES.filter((_, idx) => idx !== templateIndex);
  
  const top5 = [
    { species: selectedTemplate.name, confidence: baseConf },
    { species: otherTemplates[0]?.name || 'Other', confidence: Math.max(0.1, conf1) },
    { species: otherTemplates[1]?.name || 'Other', confidence: Math.max(0.1, conf2) },
    { species: otherTemplates[2]?.name || 'Other', confidence: Math.max(0.1, conf3) },
    { species: otherTemplates[3]?.name || 'Other', confidence: Math.max(0.1, conf4) }
  ].sort((a, b) => b.confidence - a.confidence);

  return {
    id: randomId,
    species: selectedTemplate.name,
    confidence,
    speciesGroup: selectedTemplate.group,
    health,
    age,
    foliage,
    imageQuality,
    occlusion,
    needsReview,
    timestamp: new Date().toISOString(),
    top5
  };
};
