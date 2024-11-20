export interface DatabaseConfig {
  host: string;
  port: number;
  database: string;
  user: string;
  password: string;
  ssl?: boolean;
  cert?: string;
}

export interface DatabaseConnection {
  query: (text: string, params?: any[]) => Promise<any>;
  release: () => void;
}

export interface DatabasePool {
  connect: () => Promise<DatabaseConnection>;
  end: () => Promise<void>;
}

export interface ScrapedData {
  url: string;
  title: string;
  content: string;
  fullText: string;
  createdAt?: Date;
}

export interface CrawlData {
  url: string;
  links: string[];
  seleniumRequired: boolean;
  description: string;
  errors: string[];
  additionalNotes: string;
}

export interface DeepCrawlData extends CrawlData {
  elements: string[];
  challenges: string[];
  notes: string;
  importantElements: string[];
}
