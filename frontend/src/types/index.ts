export * from './audit';
export * from './finding';
export * from './evidence';
export * from './agent';
export * from './evaluation';
export * from './repository';
export * from './changelog';
export * from './trajectory';
export * from './analysis';
export * from './health';

export interface ApiError {
  message: string;
  code?: string;
  status?: number;
}



export type AsyncState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: string };
