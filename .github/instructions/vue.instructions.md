---
description: VueJs coding style and guidelines for the project.
applyTo: "**/*.vue"
---

# Best Practices

## Style binding

Refactor inline style bindings that use ticks and template literals to use object syntax instead. This improves readability and maintainability of the code. For example, instead of using an inline expression like this:

```html
<div :style="`color: ${activeColor}; font-size: ${fontSize}px;`"></div>
```

Refactor it to use object syntax like this:

```html
<div :style="{ color: activeColor, fontSize: fontSize + 'px' }"></div>
```

All in all, you should always refactor or suggest inline style bindings to use computed properties instead of inline expressions. This improves readability and maintainability of the code. For example, instead of using an inline expression like this:

```vue
<template>
  <div :style="styleObject"></div>
</template>

<script lang="ts" setup>
const styleObject = reactive({
  color: 'red',
  fontSize: '30px'
})
</script>
```

## Getters should be side-effect free​

It is important to remember that computed getter functions should only perform pure computation and be free of side effects. For example, don't mutate other state, make async requests, or mutate the DOM inside a computed getter! Think of a computed property as declaratively describing how to derive a value based on other values - its only responsibility should be computing and returning that value. Later in the guide we will discuss how we can perform side effects in reaction to state changes with watchers.

## Avoid mutating computed value​

The returned value from a computed property is derived state. Think of it as a temporary snapshot - every time the source state changes, a new snapshot is created. It does not make sense to mutate a snapshot, so a computed return value should be treated as read-only and never be mutated - instead, update the source state it depends on to trigger new computations.

## Side effect cleanups in watchers

When using watchers to perform side effects in reaction to state changes, it is important to clean up any side effects when the watcher is re-run or stopped. This can be done by returning a cleanup function from the watcher callback. For example, if you are setting up an event listener in a watcher, you should remove that event listener when the watcher is re-run or stopped.

```vue
<script lang="ts" setup>
import { watch } from 'vue'

watch(
  () => props.someProp,
  (newValue, oldValue, onCleanup) => {
    const handleEvent = () => {
      // handle event
    }
    window.addEventListener('some-event', handleEvent)

    onCleanup(() => {
      window.removeEventListener('some-event', handleEvent)
    })
  }
)
</script>
```

Take this example with a $fetch request:

```vue
<script lang="ts" setup>
import { watch, onWatcherCleanup } from 'vue'

watch(id, (newId) => {
  const controller = new AbortController()

  fetch(`/api/${newId}`, { signal: controller.signal }).then(() => {
    // callback logic
  })

  onWatcherCleanup(() => {
    // abort stale request
    controller.abort()
  })
})
</script>
```

If `id` changes before the request completes, the previous request will still fire the callback with an ID value that is already stale. Ideally, we want to be able to cancel the stale request when `id` changes to a new value. Use the `onWatcherCleanup` API to register a cleanup function that will be called when the watcher is invalidated and is about to re-run. The same can be done with `onCleanup` in the `watch` callback:

```typescript
watch(id, (newId, oldId, onCleanup) => {
  // ...
  onCleanup(() => {
    // cleanup logic
  })
})

watchEffect((onCleanup) => {
  // ...
  onCleanup(() => {
    // cleanup logic
  })
})
```

## Accessing template refs

Prefer `useTemplateRef` over `ref` for template refs. The `useTemplateRef` function is a utility that provides a more type-safe way to access template refs in Vue 3. It ensures that the ref is properly typed and avoids potential issues with null or undefined values.

```vue
<template>
  <div ref="myDiv"></div>
</template>

<script lang="ts" setup>
import { useTemplateRef } from 'vue'

const myDiv = useTemplateRef<HTMLDivElement>('myDiv')
</script>
```

# References

* https://vuejs.org/guide/essentials/computed.html
* https://vuejs.org/guide/essentials/class-and-style.html
* https://vuejs.org/guide/essentials/watchers.html
* https://vuejs.org/guide/best-practices/performance.html
* https://vuejs.org/guide/best-practices/security.html
