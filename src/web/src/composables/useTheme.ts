import { inject, provide, type InjectionKey, type Ref } from 'vue';

export type Theme = 'dark' | 'light';

const ThemeKey: InjectionKey<Ref<Theme>> = Symbol('theme');

export function provideTheme(theme: Ref<Theme>) {
  provide(ThemeKey, theme);
}

export function useTheme(): Ref<Theme> {
  const theme = inject(ThemeKey);
  if (!theme) throw new Error('useTheme() called without provideTheme()');
  return theme;
}
