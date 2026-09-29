<template>
  <!-- Auth layout: full-page, dark background, centered content -->
  <div class="auth-layout">
    <slot />
  </div>
</template>

<style scoped>
.auth-layout {
  min-height: 100vh;
  background-color: var(--bg-base);
  display: flex;
  flex-direction: column;
}
</style>

