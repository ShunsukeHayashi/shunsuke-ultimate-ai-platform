# /extract-context

Extract hierarchical context from sources using YAML Context Engineering Agent.

## Usage

```
/extract-context [sources...]
```

## Arguments

- `sources` - One or more URLs, file paths, or text snippets to extract context from

## Description

This global command uses the YAML Context Engineering Agent MCP server to:

1. Analyze the provided sources
2. Extract hierarchical heading structures (L1, L2, L3)
3. Generate YAML frontmatter with metadata
4. Create organized context files in Markdown format
5. Save files to the configured output directory

## Configuration

The output directory is configured in the MCP server settings:
- Default: `/Users/shunsuke/Dev/Dev_Claude/generated_contexts`
- Can be overridden with environment variable: `MCP_OUTPUT_DIRECTORY`

## Examples

```
/extract-context https://docs.example.com/api
/extract-context ~/Documents/notes.md
/extract-context "Raw text to analyze"
```

## Implementation

```javascript
const args = "$ARGUMENTS".trim();
if (!args) {
    console.error("❌ エラー: ソースを指定してください");
    console.log("使用方法: /extract-context <URL|file|text>");
    process.exit(1);
}

// Use MCP tools for extraction
const sources = args.split(/\s+/);
console.log("🚀 コンテキスト抽出を開始します");
console.log(`📍 ソース: ${sources.length}個`);

// Call MCP tools
for (const source of sources) {
    const urlPattern = /^https?:\/\//;
    const isUrl = urlPattern.test(source);
    
    if (isUrl) {
        // Use web_content_fetcher
        await mcp.call("yaml-context-engineering", "web_content_fetcher", {
            urls: [source],
            timeout: 30
        });
    }
    
    // Extract structure
    await mcp.call("yaml-context-engineering", "llm_structure_extractor", {
        content: content,
        extraction_config: {
            granularity: "L1_L2",
            summarization: "detailed"
        }
    });
    
    // Generate and save file
    await mcp.call("yaml-context-engineering", "file_system_manager", {
        action: "write_file",
        path: outputPath,
        content: structuredContent
    });
}

console.log("✅ コンテキスト抽出が完了しました！");
```

## Error Handling

- **無効なURL**: URLの形式をチェックし、エラーメッセージを表示
- **ファイルが見つからない**: ファイルの存在を確認し、適切なエラーを表示
- **ネットワークエラー**: 3回までリトライし、失敗時は詳細なエラー情報を提供
- **構造抽出エラー**: フォールバックとして基本的な構造抽出を実行

## Related Commands

- `/setup-project` - Initialize a new YAML Context Engineering project
- `/generate-agent` - Create specialized extraction agents
- `/analyze-quality` - Analyze the quality of extracted contexts