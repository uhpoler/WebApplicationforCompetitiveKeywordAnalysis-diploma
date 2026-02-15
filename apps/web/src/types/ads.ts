/** Location/country for filtering ads */
export interface Location {
  location_code: number
  location_name: string
  country_iso_code: string
}

/** Response from the locations endpoint */
export interface LocationsResponse {
  locations: Location[]
}

/** Language for filtering ads */
export interface Language {
  code: string
  name: string
}

/** Response from the languages endpoint */
export interface LanguagesResponse {
  languages: Language[]
}

/** Preview image data for an ad */
export interface PreviewImage {
  url: string | null
  width: number | null
  height: number | null
}

/** Extracted text content from an ad */
export interface AdTextContent {
  headline: string | null
  description: string | null
  sitelinks: string[]
  raw_text: string | null
  keyphrases: string[]
  detected_language: string | null
  error: string | null
}

/** Ad item with extracted text content */
export interface AdItem {
  type: string
  rank_group: number | null
  rank_absolute: number | null
  advertiser_id: string | null
  creative_id: string | null
  title: string | null
  url: string | null
  verified: boolean | null
  format: string | null
  preview_image: PreviewImage | null
  first_shown: string | null
  last_shown: string | null
  text_content: AdTextContent | null
}

/** Information about a keyphrase and its source ad */
export interface PhraseInfo {
  phrase: string
  ad_title: string | null
  ad_url: string | null
  creative_id: string | null
}

/** A cluster of related keyphrases */
export interface Cluster {
  id: number
  name: string
  size: number
  phrases: PhraseInfo[]
}

/** Clustering result data */
export interface ClusteringData {
  clusters: Cluster[]
  unclustered: PhraseInfo[]
  total_phrases: number
  error: string | null
}

/** Response from the domain ads search endpoint */
export interface AdsSearchResponse {
  domain: string
  ads_count: number
  ads: AdItem[]
  clustering: ClusteringData | null
}

/** Parameters for searching ads */
export interface AdsSearchParams {
  domain: string
  depth: number
  locationCode: number
  language: string | null
}
