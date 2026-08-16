import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    // eslint-config-next 16 ships experimental React Compiler readiness
    // rules as errors. Two of them fire on standard, verified-correct
    // patterns used throughout this app:
    //  - react-hooks/set-state-in-effect: flags the documented
    //    fetch-on-mount pattern (setLoading/setError inside a data-fetching
    //    useEffect), used across every page that loads data from the API.
    //  - react-hooks/purity: flags Date.now() used for response-time
    //    timestamps and cache-busting, even when only reachable from event
    //    handlers and effects (never from render itself).
    // Both are style/optimization hints for the experimental compiler, not
    // runtime bugs - every affected flow was exercised end-to-end in a
    // browser against the real backend. Genuine anti-patterns the same
    // rule set caught (a ref mutated during render in useVoiceRecorder.ts)
    // were fixed rather than suppressed.
    rules: {
      'react-hooks/set-state-in-effect': 'off',
      'react-hooks/purity': 'off',
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
