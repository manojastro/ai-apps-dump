/** Shared types for Exa → Azure Grok live search flow. */

export interface LiveSearchSource {
  title: string;
  url: string;
  publishedDate: string | null;
  highlights: string[];
}

export interface LiveSearchCitation {
  id: number;
  title: string;
  url: string;
  publishedDate: string | null;
}

export interface LiveSearchRequest {
  query: string;
}

export interface LiveSearchResponse {
  answer: string;
  citations: LiveSearchCitation[];
}

export interface LiveSearchErrorBody {
  error: string;
  code?: string;
}

/** Safe provider error with HTTP status for API route mapping. */
export class ProviderError extends Error {
  readonly status: number;
  readonly provider: "exa" | "azure" | "internal";
  readonly code?: string;
  readonly requestId?: string;

  constructor(
    message: string,
    options: {
      status: number;
      provider: "exa" | "azure" | "internal";
      code?: string;
      requestId?: string;
      cause?: unknown;
    }
  ) {
    super(message, options.cause !== undefined ? { cause: options.cause } : undefined);
    this.name = "ProviderError";
    this.status = options.status;
    this.provider = options.provider;
    this.code = options.code;
    this.requestId = options.requestId;
  }
}
