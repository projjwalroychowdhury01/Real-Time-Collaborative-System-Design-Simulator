// TypeScript types for the design canvas domain

export type ComponentType =
  | 'api_gateway'
  | 'microservice'
  | 'database'
  | 'cache'
  | 'queue'
  | 'load_balancer'
  | 'cdn'
  | 'storage';

export interface DesignComponent {
  id: string;
  type: ComponentType;
  label: string;
  x: number;        // canvas position
  y: number;
  replicas: number;
  throughput: number;   // max req/s
  latency_ms: number;
}

export interface DesignEdge {
  id: string;
  from: string;   // component id
  to: string;
  weight: number;
  label?: string;
}

export interface DesignJSON {
  components: DesignComponent[];
  edges: DesignEdge[];
}

export interface Design {
  id: number;
  name: string;
  description?: string;
  design_json: DesignJSON;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}
