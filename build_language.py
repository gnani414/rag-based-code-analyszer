from tree_sitter import Language

Language.build_library(
    'build/my-languages.dll',
    [
        'vendor/tree-sitter-java',
        'vendor/tree-sitter-python',

    ]
)

