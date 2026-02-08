# Job Hunter Package

# Shared constants used by multiple modules (ai_analyzer, resume_validator)
TRANSFERABLE_SKIP_WORDS = frozenset({
    'jd', 'mentions', 'or', 'but', 'not', 'as', 'primary', 'for', 'when',
    'api', 'development', 'tracking', 'event', 'streaming', 'ml', 'demos',
    'experiment',
})