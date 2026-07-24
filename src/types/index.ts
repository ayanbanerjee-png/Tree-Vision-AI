export type HealthStatus = 'Healthy' | 'Mild Decline' | 'Severe Disease';
export type TreeAge = 'Young' | 'Semi-Mature' | 'Mature' | 'Ancient';
export type FoliageDensity = 'Full Canopy' | 'Moderate' | 'Sparse' | 'None';
export type ImageQualityLevel = 'Clear' | 'Blurry' | 'Low Light';
export type OcclusionLevel = 'No' | 'Partial' | 'Heavy';

export interface SpeciesPrediction {
  species: string;
  confidence: number;
}

export interface TreeAnalysis {
  id: string;
  species: string;
  rawSpecies?: string;
  confidence: number;
  speciesGroup: string;
  health: HealthStatus;
  age: TreeAge;
  foliage: FoliageDensity;
  imageQuality: ImageQualityLevel;
  occlusion: OcclusionLevel;
  needsReview: boolean;
  timestamp: string;
  imageUrl?: string;
  croppedImageUrl?: string;
  top5: SpeciesPrediction[];
}

export interface DashboardStats {
  imagesProcessed: number;
  avgConfidence: number;
  needsReviewCount: number;
  healthyTreesCount: number;
}

export interface BatchItem {
  id: string;
  name: string;
  size: number;
  progress: number; // 0 to 100
  status: 'pending' | 'processing' | 'completed' | 'failed';
  result?: TreeAnalysis;
  file?: File;
}
