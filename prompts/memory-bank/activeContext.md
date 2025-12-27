# Active Context

## Current Focus
The Memory Bank structure has just been established. The focus is now on maintaining this documentation as development proceeds on Phase 1 of Spyfall Arena.
Recently completed **Rate Limiting** implementation to prevent `RESOURCE_EXHAUSTED` errors.

## Recent Changes
-   **Documentation**: Initialized the Memory Bank in `prompts/memory-bank`.
-   **Phase 1 Development**: Core game engine implemented (Rules, Roles, Q/A, Voting, Config, Logging).
-   **Robustness**: Implemented Token Bucket rate limiter for Gemini API.
-   **Architecture**: `src` layout and `game_logging` are stable.

## Active Decisions
-   **Documentation Strategy**: Using the "Memory Bank" pattern to maintain project context.
-   **Testing Strategy**: Strictly unit tests with mocks.
-   **Logging**: `game_logging` module handles all output.

## Next Steps
1.  Implement basic evaluation metrics (Phase 1).
2.  Begin planning for Phase 2 (Tournament automation).
