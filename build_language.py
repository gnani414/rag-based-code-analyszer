from tree_sitter import Language

Language.build_library(
    'build/my-languages.dll',
    [
        'vendor/tree-sitter-java',
        'vendor/tree-sitter-python',
        'vendor/tree-sitter-c',
        'vendor/tree-sitter-javascript',
         'vendor/tree-sitter-javascript',
    ]
)

