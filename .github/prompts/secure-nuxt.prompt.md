---
agent: 'ask'
model: Claude Sonnet 4
description: 'Perform package and security checks on Nuxt/Vue apps'
---
* Collect the `packages.json` in the current directory and check for known vulnerabilities.
* Ensure that packages in required packages are installed and up to date. If they are not present, install them, if they are outdated, update them to the latest stable versions.

**required packages**

```json
{
    "@faker-js/faker": "^10.5.0",
    "@nuxtjs/seo": "^5.3.2",
    "@nuxt/kit": "^4.4.8",
    "@nuxt/scripts": "^1.3.0",
    "@nuxt/test-utils": "^4.0.3",
    "@nuxtjs/i18n": "^10.4.1",
    "@takumi-rs/core": "^2.0.3",
    "@takumi-rs/wasm": "^2.0.3",
    "@testing-library/vue": "^8.1.0",
    "@vercel/analytics": "^2.0.1",
    "@vercel/speed-insights": "^2.0.0",
    "@vitest/coverage-v8": "^4.1.10",
    "@vitest/ui": "4.1.10",
    "@vue/test-utils": "^2.4.11",
    "@vueuse/core": "^14.3.0",
    "@vueuse/integrations": "^14.3.0",
    "@vueuse/math": "14.3.0",
    "@vueuse/motion": "3.0.3",
    "@vueuse/nuxt": "^14.3.0",
    "happy-dom": "^20.10.6",
    "oxfmt": "^0.58.0",
    "oxlint": "^1.73.0",
    "oxlint-tsgolint": "^0.24.0",
    "vitest": "^4.1.10",
    "zod": "^4.4.3"
}
```
