/**
 * Lightweight logger — noops in production, delegates to console in dev.
 *
 * Use instead of `console.log` so production bundles don't leak developer
 * breadcrumbs. `logger.error` stays enabled everywhere because surfaced
 * errors are expected to reach the user / a reporter.
 */
const isDev = import.meta.env.DEV;

type Args = unknown[];

export const logger = {
  debug: (...args: Args): void => {
    if (isDev) {
      // eslint-disable-next-line no-console
      console.debug(...args);
    }
  },
  info: (...args: Args): void => {
    if (isDev) {
      // eslint-disable-next-line no-console
      console.info(...args);
    }
  },
  warn: (...args: Args): void => {
    if (isDev) {
      // eslint-disable-next-line no-console
      console.warn(...args);
    }
  },
  error: (...args: Args): void => {
    // Errors always emit — prod error reporter can hook in here.
    // eslint-disable-next-line no-console
    console.error(...args);
  },
};

export type Logger = typeof logger;
