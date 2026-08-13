export class MasterbrainApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
    readonly details?: unknown,
  ) {
    super(message);
    this.name = 'MasterbrainApiError';
  }
}

export class MasterbrainContractError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'MasterbrainContractError';
  }
}

export class WorkspaceConflictError extends Error {
  constructor(
    message: string,
    readonly paths: readonly string[],
  ) {
    super(message);
    this.name = 'WorkspaceConflictError';
  }
}
