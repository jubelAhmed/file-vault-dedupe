export interface File {
  id: string;
  original_filename: string;
  file_type: string;
  size: number;
  uploaded_at: string;
  file: string;
  file_url?: string;
  is_duplicate?: boolean;
  user_id?: string;
  file_hash?: string;
  reference_count?: number;
  is_reference?: boolean;
  original_file?: string;
} 