# DCC Shelves Internationalization (i18n) Design

## 1. Technology Selection

### Recommended Solution: react-i18next

| Feature | react-i18next | react-intl | 
|---------|--------------|------------|
| Bundle Size | ~15KB | ~25KB |
| Offline Support | ✅ Excellent | ✅ Good |
| React 19 Support | ✅ | ✅ |
| TypeScript | ✅ Full | ✅ Full |
| Caching | ✅ Plugins | ❌ Manual |
| Learning Curve | Easy | Medium |
| Community | Very Active | Active |

**Selection Reason:** react-i18next provides:
- Built-in caching plugin (`i18next-localstorage-backend`)
- Browser language detection (`i18next-browser-languagedetector`)
- Complete offline support with local JSON files
- Smaller bundle size and simpler API
- Excellent TypeScript integration

### Packages to Install
```bash
npm install i18next react-i18next i18next-browser-languagedetector
```

## 2. Caching Strategy

### Primary: LocalStorage (Recommended for this project)
- **Why not IndexedDB?** Translation data is small (< 100KB), LocalStorage is simpler and faster
- **Why not Pinia?** This is React project, not Vue; use React Context instead
- **Cache Key Format:** `i18next_res_{lng}_{ns}`
- **Cache Expiry:** 7 days (configurable)

### Caching Flow
```
User Request → Check LocalStorage → Cache Hit? → Use cached
                                  → Cache Miss? → Load from JSON → Store in LocalStorage
```

## 3. File Structure

```
src/frontend/
├── i18n/
│   ├── index.ts              # i18n configuration
│   ├── locales/
│   │   ├── en/
│   │   │   └── translation.json
│   │   └── zh/
│   │       └── translation.json
│   └── types.ts              # TypeScript types for translations
```

## 4. Translation Keys Convention

### Namespace Structure
```json
{
  "common": {
    "search": "Search",
    "cancel": "Cancel",
    "save": "Save"
  },
  "app": {
    "title": "DCC Shelves",
    "devMode": "Dev Mode"
  },
  "tools": {
    "allTools": "All Tools",
    "noTools": "No tools found",
    "searchPlaceholder": "Search tools..."
  },
  "console": {
    "title": "Console",
    "noLogs": "No logs to display",
    "enterCommand": "Enter command..."
  },
  "context": {
    "openLocation": "Open Location",
    "copyPath": "Copy Path",
    "viewSource": "View Source",
    "details": "Details"
  },
  "banner": {
    "settings": "Banner Settings"
  },
  "footer": {
    "host": "Host"
  }
}
```

## 5. Language Detection Priority

1. URL query parameter (`?lng=zh`)
2. LocalStorage saved preference
3. Browser navigator language
4. Default fallback: English (en)

## 6. Supported Languages (Initial)

| Code | Language | Status |
|------|----------|--------|
| en | English | Default |
| zh | Chinese (Simplified) | Primary |

## 7. Implementation Checklist

- [x] Technical design document
- [ ] Install dependencies
- [ ] Create i18n configuration
- [ ] Create English translation file
- [ ] Create Chinese translation file
- [ ] Integrate i18n provider
- [ ] Update all components
- [ ] Create language switcher
- [ ] Add usage documentation

## 8. Usage Example

```tsx
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();
  
  return (
    <button>{t('common.save')}</button>
  );
}
```

## 9. Adding New Language

1. Create `src/frontend/i18n/locales/{lang}/translation.json`
2. Copy structure from `en/translation.json`
3. Translate all values
4. Update `src/frontend/i18n/types.ts`:
   - Add new language code to `SupportedLanguage` type
   - Add entry to `SUPPORTED_LANGUAGES` array
5. Update `src/frontend/i18n/index.ts`:
   - Import the new translation file
   - Add to `resources` object
   - Add to `supportedLngs` array

### Example: Adding Japanese (ja)

```typescript
// 1. Create src/frontend/i18n/locales/ja/translation.json
{
  "common": {
    "search": "検索",
    "cancel": "キャンセル",
    ...
  }
}

// 2. Update types.ts
export type SupportedLanguage = 'en' | 'zh' | 'ja'

export const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English', nativeName: 'English' },
  { code: 'zh', name: 'Chinese', nativeName: '中文' },
  { code: 'ja', name: 'Japanese', nativeName: '日本語' },
]

// 3. Update index.ts
import jaTranslation from './locales/ja/translation.json'

const resources = {
  en: { translation: enTranslation },
  zh: { translation: zhTranslation },
  ja: { translation: jaTranslation },
}
```

## 10. Adding New Translation Keys

1. Add the key to `en/translation.json` first (as the source of truth)
2. Add the same key to all other language files
3. Use in component: `t('namespace.key')`

### Example

```json
// en/translation.json
{
  "tools": {
    "newFeature": "New Feature"
  }
}

// zh/translation.json
{
  "tools": {
    "newFeature": "新功能"
  }
}
```

```tsx
// Component usage
const { t } = useTranslation()
return <span>{t('tools.newFeature')}</span>
```

## 11. Translation with Variables

Use interpolation for dynamic values:

```json
{
  "tools": {
    "launching": "Launching {{name}}..."
  }
}
```

```tsx
t('tools.launching', { name: toolName })
```

## 12. Best Practices

1. **Keep keys hierarchical**: Use nested objects for organization
2. **Use descriptive keys**: `button.submit` not `btn1`
3. **Avoid HTML in translations**: Keep translations text-only
4. **Test all languages**: Switch language during development
5. **Update all files together**: Never leave a language behind

