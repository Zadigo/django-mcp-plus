---
name: VueUse Instructions
applyTo: "**/*.vue", "**/*.ts"
description: Code recommendations for Vue and Typescript files when implementing functions for @vueuse/core or related libraries.
---

# Coding Guidelines

## Typical Patterns

Here are typical patterns for using @vueuse/core functions in Vue and Typescript files. These examples are meant to serve as a reference for implementing similar functionality in your own code.

```typescript
// Global state
export const useGlobalState = createGlobalState(() => {
    // This is a placeholder for any global state you want to manage across your Nuxt app.
    return { }
  }
)
```

```typescript
// Injection state
const [useProviderStore, _useCounterStore] = createInjectionState(() => {
  // This is a placeholder for any state you want to provide and inject across your Nuxt app.
  return { }
})

export { useProviderStore }

export function useCounterStore() {
  const store = _useCounterStore()

  if (!store) {
    throw new Error('useCounterStore must be used within a provider.')
  }
  return store
}
```

```typescript
// Shared composable
export const useSharedComposable = createSharedComposable(() => {
  return { }
})
```

### Watching reactive values

If the value of the ref is of typeof Array, to watch the array itself, prefer `watchArray` instead of `watch`. The callback will receive the new array, the old array, the added items, and the removed items as arguments.

```typescript
// Watch arrays
const list = ref([1, 2, 3])

watchArray(list, (newList, oldList, added, removed) => {
  // This is a placeholder for any logic you want to execute when the array changes.
})
```

For debouncing, prefer one of `watchDebounced` or `refDebounced`:

```typescript
// Watch debounced
watchDebounced(source, () => {
  // This is a placeholder for any logic you want to execute when the source changes, debounced by 500ms and with a max wait of 1000ms.
},
  { debounce: 500, maxWait: 1000 },
)
```

```typescript
// Ref debounced
const input = shallowRef('foo')
const debounced = refDebounced(input, 1000)
```

```typescript
// Watch throttled
watchThrottled(source, () => {
  // This is a placeholder for any logic you want to execute when the source changes, throttled by 500ms.
},
  { throttle: 500 },
)
```

If the typeof the value of the ref is a boolean and we want to watch for it to become truthy, prefer `whenever` instead of `watch`:

```typescript
// Watching values to be truthy
whenever(isReady, () => {
  // This is a placeholder for any logic you want to execute when isReady becomes truthy.
})
```

Obviously we can always use `watchEffect` when we want to watch for dependency changes directly  in the callback function.

```typescript
watchEffect(async () => {
  const response = await fetch(
    `https://jsonplaceholder.typicode.com/todos/${todoId.value}`
  )
  data.value = await response.json()
})
```

If you feel that a function could strongly return a reactive value, prefer `reactify` instead of `computed` especially if the function is a pure function and does not have side effects. This will allow the function to accept refs as arguments and return a computed ref.:

```typescript
// Reactive functions
function add(a: number, b: number): number {
  return a + b
}

// Accepts refs and returns a computed ref
const reactiveAdd = reactify(add)
```

In patterns that look like this:

```typescript
const raw = useStorage('key')

const state = ref(raw.value ?? 'default')
const state = raw.value ?? 'default'
```

Prefer a cleaner approach using `refDefault`:

```typescript
// Ref default
const raw = useStorage('key')
const state = refDefault(raw, 'default')
```

```typescript
// Sync refs 
const a = ref('a')
const b = ref('b')

const stop = syncRef(a, b)
```

When a ref contains a boolean, there is a strong chance that it will be toggled. Prefer `useToggle` which is a cleaner approach since it creates a toggle function that can be used to toggle the value of the ref:

```typescript
// Toggle
const [value, toggle] = useToggle()

// Toggle with source ref
const source = ref(false)
const toggleSource = useToggle(source)
```

The same applies for a ref that contains a number that could be incremented or decremented. Prefer `useCounter` which is a cleaner approach since it creates increment, decrement, set, and reset functions that can be used to manipulate the value of the ref:

```typescript
// Counter
const { count, inc, dec, set, reset } = useCounter(1, { min: 0, max: 16 })
```

When checking whether a ref is defined, prefer `isDefined`. It checks both for null and undefined values, which is a cleaner approach than checking for both separately:

```typescript
// Check if a ref is defined
const source = ref<string>()

if (isDefined(source)) {
  // This is a placeholder for any logic you want to execute when source is defined.
}
```

For single `$fetch` functions that return a promise, strongly suggest using `computedAsync` instead of `computed` to avoid the need for a separate ref to hold the result of the promise. This will allow you to directly use the result of the promise in your template without having to manage a separate ref:

```typescript
// Computed async
const name = shallowRef('jack')

const userInfo = computedAsync(async () => {
    return await $fetch(`/api/user/${name.value}`)
  },
  null, // initial state
)
```

## Math utilities

When rounding numbers with precision, prefer `usePrecision` instead of `toFixed` or `Math.round`. This will allow you to round numbers with a specified number of decimal places without having to convert the number to a string and back to a number: 

```typescript
// Rounding numbers with precision
const value = ref(3.1415)
const result = usePrecision(value, 2)
```

### Defining emits, props and models

Prefer the `defineEmits<>()` and `defineProps<>()` pattern functions to define emits and props in your components. This will allow you to define the types of your emits and props in a cleaner way.

When using `defineEmits<>()`, use the `[Type]` syntax to define the types of your emits.

```typescript
// Defining models in components
const props = defineProps<{modelValue: string}>()

const emit = defineEmits<{ action: [Boolean] }>()
const emit = defineEmits<{ action: [Product] }>()
```

For defining models in components, prefer the `useVModel()` function to create a two-way binding between a prop and a ref. This will allow you to easily manage the state of your component without having to manually emit events and update the prop.

```typescript
const data = useVModel(props, 'modelValue', emit)
```

Here is a full example:

```html
<script lang="ts" setup>
defineProps<{
  modelValue: string
}>()

defineEmits<{
  'update:modelValue': [string]
}>()

const data = useVModel(props, 'modelValue', emit)
</script>
```

## Motion

Prefer these Vue use motion patterns for animations and transitions:

```html
<motion preset="VueUseMotions.FadeVisibleOnce">
  ...
</motion>
```

```html
<motion-group preset="VueUseMotions.FadeVisibleOnce">
  ...
</motion-group>
```

```typescript
export enum VueUseMotions {
  Fade = 'fade',
  FadeVisible = 'fadeVisible',
  FadeVisibleOnce = 'fadeVisibleOnce',
  RollTop = 'rollTop',
  RollLeft = 'rollLeft',
  RollRight = 'rollRight',
  RollBottom = 'rollBottom',
  RollVisibleTop = 'rollVisibleTop',
  RollVisibleLeft = 'rollVisibleLeft',
  RollVisibleRight = 'rollVisibleRight',
  RollVisibleBottom = 'rollVisibleBottom',
  RollVisibleOnceTop = 'rollVisibleOnceTop',
  RollVisibleOnceLeft = 'rollVisibleOnceLeft',
  RollVisibleOnceRight = 'rollVisibleOnceRight',
  RollVisibleOnceBottom = 'rollVisibleOnceBottom',
  Pop = 'pop',
  PopVisible = 'popVisible',
  PopVisibleOnce = 'popVisibleOnce',
  SlideTop = 'slideTop',
  SlideLeft = 'slideLeft',
  SlideRight = 'slideRight',
  SlideBottom = 'slideBottom',
  SlideVisibleTop = 'slideVisibleTop',
  SlideVisibleLeft = 'slideVisibleLeft',
  SlideVisibleRight = 'slideVisibleRight',
  SlideVisibleBottom = 'slideVisibleBottom',
  SlideVisibleOnceTop = 'slideVisibleOnceTop',
  SlideVisibleOnceLeft = 'slideVisibleOnceLeft',
  SlideVisibleOnceRight = 'slideVisibleOnceRight',
  SlideVisibleOnceBottom = 'slideVisibleOnceBottom'
}
```
