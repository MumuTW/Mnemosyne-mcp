"""
Mnemosyne MCP CLI 主入口

提供命令行工具的基本功能。
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import click

from ..core.config import get_settings, validate_config
from ..core.logging import setup_logging
from ..drivers.falkordb_driver import FalkorDBDriver


async def test_llm_connection():
    """測試 LLM 連接"""
    try:
        import os

        from ..llm.providers.openai_provider import OpenAIProvider

        # 嘗試 OpenAI 連接
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                provider = OpenAIProvider(api_key=openai_key)
                # 測試簡單的 API 調用
                await provider.generate_text("測試連接", max_tokens=10)
                click.echo("✅ OpenAI API 連接正常")
            except Exception as e:
                click.echo(f"❌ OpenAI API 連接失敗: {str(e)[:100]}...")

        # 可以添加更多 LLM 提供商的測試

    except ImportError:
        click.echo("⚠️  LLM 模組未完全安裝，跳過連接測試")
    except Exception as e:
        click.echo(f"❌ LLM 連接測試失敗: {e}")


@click.group()
@click.option("--config", "-c", help="配置文件路徑")
@click.option("--verbose", "-v", is_flag=True, help="詳細輸出")
@click.pass_context
def cli(ctx, config: Optional[str], verbose: bool):
    """Mnemosyne MCP 命令行工具"""
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    ctx.obj["verbose"] = verbose

    # 設置日誌
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(level=log_level, format_type="console")


@cli.command()
@click.pass_context
def doctor(ctx):
    """診斷系統配置和環境"""
    click.echo("🔍 Mnemosyne MCP 系統診斷")
    click.echo("=" * 50)

    # 檢查配置
    try:
        settings = get_settings()
        click.echo(f"✅ 配置加載成功 (環境: {settings.environment})")

        # 驗證配置
        errors = validate_config(settings)
        if errors:
            click.echo("❌ 配置驗證失敗:")
            for error in errors:
                click.echo(f"   - {error}")
            return
        else:
            click.echo("✅ 配置驗證通過")

    except Exception as e:
        click.echo(f"❌ 配置加載失敗: {e}")
        return

    # 檢查資料庫連接
    click.echo("\n🔗 檢查資料庫連接...")

    async def check_database():
        try:
            db_config = settings.database.to_connection_config()
            client = FalkorDBDriver(db_config)
            await client.connect()

            # 執行測試查詢
            result = await client.execute_query("RETURN 1 as test")
            if not result.is_empty:
                click.echo("✅ 資料庫連接正常")

                # 獲取健康檢查信息
                health = await client.healthcheck()
                click.echo(f"   - 主機: {health.get('host')}")
                click.echo(f"   - 端口: {health.get('port')}")
                click.echo(f"   - 資料庫: {health.get('database')}")
                click.echo(f"   - 響應時間: {health.get('response_time_ms', 0):.2f}ms")
            else:
                click.echo("❌ 資料庫測試查詢失敗")

            await client.disconnect()

        except Exception as e:
            click.echo(f"❌ 資料庫連接失敗: {e}")

    asyncio.run(check_database())

    # 檢查端口可用性
    click.echo("\n🌐 檢查端口可用性...")
    import socket

    def check_port(host: str, port: int, name: str):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex((host, port))
                if result == 0:
                    click.echo(f"⚠️  {name} 端口 {port} 已被占用")
                else:
                    click.echo(f"✅ {name} 端口 {port} 可用")
        except Exception as e:
            click.echo(f"❌ 檢查 {name} 端口失敗: {e}")

    check_port(settings.api.host, settings.api.port, "API")
    check_port(settings.api.host, settings.api.grpc_port, "gRPC")

    # 檢查環境變數和配置
    click.echo("\n🔧 檢查環境配置...")

    # 檢查 .env 文件
    env_file = Path(".env")
    if env_file.exists():
        click.echo("✅ .env 文件存在")
    else:
        click.echo("⚠️  .env 文件不存在")
        click.echo("   建議複製 .env.example 並配置必要的變數")

    # 檢查關鍵環境變數
    import os

    critical_vars = [
        ("FALKORDB_HOST", "FalkorDB 主機"),
        ("FALKORDB_PORT", "FalkorDB 端口"),
    ]

    optional_vars = [
        ("OPENAI_API_KEY", "OpenAI API 金鑰"),
        ("OPENROUTER_API_KEY", "OpenRouter API 金鑰"),
    ]

    click.echo("\n📋 關鍵環境變數:")
    for var, desc in critical_vars:
        value = os.getenv(var)
        if value:
            click.echo(f"✅ {desc} ({var}): 已設定")
        else:
            click.echo(f"⚠️  {desc} ({var}): 未設定，將使用預設值")

    click.echo("\n🔑 LLM API 配置:")
    has_llm_key = False
    for var, desc in optional_vars:
        value = os.getenv(var)
        if value:
            # 只顯示前幾個字符，保護隱私
            masked_value = value[:8] + "..." if len(value) > 8 else "***"
            click.echo(f"✅ {desc} ({var}): {masked_value}")
            has_llm_key = True
        else:
            click.echo(f"❌ {desc} ({var}): 未設定")

    if not has_llm_key:
        click.echo("\n⚠️  警告: 未找到任何 LLM API 金鑰")
        click.echo("   某些功能可能無法正常運作")
        click.echo("   請在 .env 文件中設定 OPENAI_API_KEY 或 OPENROUTER_API_KEY")

    # 測試 LLM 連接
    if has_llm_key:
        click.echo("\n🤖 測試 LLM 連接...")
        asyncio.run(test_llm_connection())

    click.echo("\n🎉 診斷完成!")


@cli.command()
@click.option("--host", default=None, help="API 主機地址")
@click.option("--port", default=None, type=int, help="API 端口")
@click.option("--reload", is_flag=True, help="開發模式（自動重載）")
def serve(host: Optional[str], port: Optional[int], reload: bool):
    """啟動 API 服務器"""
    import uvicorn

    settings = get_settings()

    # 使用命令行參數覆蓋配置
    api_host = host or settings.api.host
    api_port = port or settings.api.port

    click.echo("🚀 啟動 Mnemosyne MCP API 服務器")
    click.echo(f"   - 地址: http://{api_host}:{api_port}")
    click.echo(f"   - 環境: {settings.environment}")
    click.echo(f"   - 重載: {'是' if reload else '否'}")

    uvicorn.run(
        "mnemosyne.api.main:app",
        host=api_host,
        port=api_port,
        reload=reload,
        log_config=None,
    )


@cli.command()
@click.option(
    "--transport", default="stdio", type=click.Choice(["stdio"]), help="MCP 傳輸方式"
)
@click.option("--debug", is_flag=True, help="除錯模式")
@click.pass_context
def serve_mcp(ctx, transport: str, debug: bool):
    """啟動 MCP 伺服器 (Model Context Protocol)

    這個命令啟動 Mnemosyne MCP 伺服器，使其能與 Claude Desktop 等 MCP 客戶端整合。

    使用範例:
    - 基本啟動: mnemo serve-mcp
    - 除錯模式: mnemo serve-mcp --debug

    配置 Claude Desktop:
    在 ~/.claude/claude_desktop_config.json 中新增:
    {
      "mcpServers": {
        "mnemosyne": {
          "command": "mnemo",
          "args": ["serve-mcp"]
        }
      }
    }
    """
    try:
        # 設定除錯模式的日誌
        if debug:
            import logging

            logging.basicConfig(
                level=logging.DEBUG,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                stream=sys.stderr,
            )

        click.echo("🚀 啟動 Mnemosyne MCP 伺服器", err=True)
        click.echo(f"   - 傳輸方式: {transport}", err=True)
        click.echo(f"   - 除錯模式: {'是' if debug else '否'}", err=True)
        click.echo(f"   - 程序 ID: {os.getpid()}", err=True)
        click.echo("", err=True)

        # 檢查必要條件
        click.echo("🔍 檢查系統狀態...", err=True)

        # 檢查 gRPC 服務連通性
        async def check_grpc_connection():
            try:
                settings = get_settings()
                from ..mcp_adapter.grpc_bridge import GrpcBridge

                bridge = GrpcBridge(settings)
                await bridge.connect()
                is_healthy = await bridge.health_check()
                await bridge.disconnect()

                if is_healthy:
                    click.echo("✅ gRPC 服務連線正常", err=True)
                    return True
                else:
                    click.echo("⚠️  gRPC 服務連線異常", err=True)
                    return False

            except Exception as e:
                click.echo(f"❌ gRPC 服務檢查失敗: {e}", err=True)
                return False

        # 執行連線檢查
        grpc_ok = asyncio.run(check_grpc_connection())

        if not grpc_ok:
            click.echo("", err=True)
            click.echo("💡 建議檢查:", err=True)
            click.echo("   1. gRPC 服務是否運行 (預設 port 50052)", err=True)
            click.echo("   2. 執行 'mnemo doctor' 進行系統診斷", err=True)
            click.echo("   3. 確認 FalkorDB 是否運行", err=True)
            click.echo("", err=True)
            click.echo("⚠️  MCP 伺服器將啟動但功能可能受限", err=True)

        click.echo("🎯 MCP 伺服器啟動中...", err=True)
        click.echo("   (使用 Ctrl+C 停止伺服器)", err=True)
        click.echo("", err=True)

        # 導入並啟動 MCP 伺服器
        async def run_mcp_server():
            from ..mcp_adapter.server import create_mcp_server

            settings = get_settings()
            server = await create_mcp_server(settings)

            # 在 stderr 顯示伺服器資訊
            info = server.get_server_info()
            click.echo("📋 伺服器資訊:", err=True)
            click.echo(f"   - 名稱: {info['name']}", err=True)
            click.echo(f"   - 版本: {info['version']}", err=True)
            click.echo(f"   - 工具數量: {info['tools_count']}", err=True)
            click.echo(f"   - 可用工具: {', '.join(info['tools'])}", err=True)
            click.echo("", err=True)
            click.echo("✅ MCP 伺服器準備就緒，等待客戶端連線...", err=True)

            # 啟動伺服器 (將阻塞在此處)
            server.run(transport=transport)

        # 執行 MCP 伺服器
        asyncio.run(run_mcp_server())

    except KeyboardInterrupt:
        click.echo("\n👋 MCP 伺服器已停止", err=True)
    except ImportError as e:
        click.echo(f"❌ MCP 依賴缺失: {e}", err=True)
        click.echo("請執行: uv sync", err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(f"❌ MCP 伺服器啟動失敗: {e}", err=True)
        if debug:
            import traceback

            click.echo(traceback.format_exc(), err=True)
        ctx.exit(1)


@cli.command()
def version():
    """顯示版本信息"""
    from .. import __description__, __version__

    click.echo(f"Mnemosyne MCP v{__version__}")
    click.echo(__description__)


@cli.command()
@click.argument("query")
@click.option(
    "--format",
    "output_format",
    default="table",
    type=click.Choice(["table", "json", "csv"]),
    help="輸出格式",
)
def query(query: str, output_format: str):
    """執行 Cypher 查詢"""
    click.echo(f"🔍 執行查詢: {query}")

    async def run_query():
        try:
            settings = get_settings()
            db_config = settings.database.to_connection_config()
            client = FalkorDBDriver(db_config)
            await client.connect()

            result = await client.execute_query(query)

            if result.is_empty:
                click.echo("📭 查詢無結果")
            else:
                click.echo(
                    f"📊 查詢結果 ({result.count} 行, {result.execution_time_ms:.2f}ms):"
                )

                if output_format == "json":
                    import json

                    click.echo(json.dumps(result.data, indent=2, ensure_ascii=False))
                elif output_format == "csv":
                    import csv
                    import io

                    if result.data:
                        output = io.StringIO()
                        writer = csv.DictWriter(
                            output, fieldnames=result.data[0].keys()
                        )
                        writer.writeheader()
                        writer.writerows(result.data)
                        click.echo(output.getvalue())
                else:  # table format
                    from tabulate import tabulate

                    if result.data:
                        headers = result.data[0].keys()
                        rows = [list(row.values()) for row in result.data]
                        click.echo(tabulate(rows, headers=headers, tablefmt="grid"))

            await client.disconnect()

        except Exception as e:
            click.echo(f"❌ 查詢執行失敗: {e}")

    asyncio.run(run_query())


@cli.group()
def atlassian():
    """Atlassian 知識圖譜管理命令"""
    pass


@cli.command()
@click.option("--project-name", default="demo-project", help="示範專案名稱")
@click.option("--clear-existing", is_flag=True, help="清除現有資料")
def seed(project_name: str, clear_existing: bool):
    """載入示範資料和範例專案"""
    click.echo("🌱 載入示範資料...")
    click.echo(f"   - 專案名稱: {project_name}")
    click.echo(f"   - 清除現有: {'是' if clear_existing else '否'}")

    async def run_seeding():
        try:
            settings = get_settings()
            db_config = settings.database.to_connection_config()
            client = FalkorDBDriver(db_config)
            await client.connect()

            # 清除現有資料（如果指定）
            if clear_existing:
                click.echo("\n🗑️  清除現有資料...")
                await client.execute_query("MATCH (n) DETACH DELETE n")
                click.echo("✅ 資料清除完成")

            # 建立示範項目節點
            click.echo("\n📁 建立示範專案...")
            project_query = f"""
            CREATE (p:Project {{
                id: '{project_name}',
                name: '{project_name}',
                description: 'Mnemosyne MCP 示範專案',
                created_at: datetime(),
                repository_url: 'https://github.com/example/{project_name}',
                language: 'Python',
                framework: 'FastAPI'
            }})
            RETURN p
            """
            await client.execute_query(project_query)

            # 建立示範文件節點
            click.echo("📄 建立示範文件...")
            files_data = [
                ("main.py", "Application entry point", "src/", "python"),
                ("config.py", "Configuration management", "src/core/", "python"),
                ("database.py", "Database connection", "src/db/", "python"),
                ("api.py", "REST API endpoints", "src/api/", "python"),
                ("models.py", "Data models", "src/models/", "python"),
                ("README.md", "Project documentation", "", "markdown"),
                ("requirements.txt", "Python dependencies", "", "text"),
            ]

            for filename, description, path, file_type in files_data:
                full_path = f"{path}{filename}"
                file_query = f"""
                MATCH (p:Project {{id: '{project_name}'}})
                CREATE (f:File {{
                    id: '{full_path}',
                    name: '{filename}',
                    path: '{full_path}',
                    description: '{description}',
                    type: '{file_type}',
                    size: {100 + len(filename) * 10},
                    lines: {50 + len(filename) * 2},
                    created_at: datetime()
                }})
                CREATE (p)-[:CONTAINS]->(f)
                RETURN f
                """
                await client.execute_query(file_query)

            # 建立示範函數節點
            click.echo("⚙️  建立示範函數...")
            functions_data = [
                ("main", "main.py", "Application entry point", 1, 20),
                ("get_config", "config.py", "Load configuration", 10, 25),
                ("connect_db", "database.py", "Connect to database", 5, 15),
                ("health_check", "api.py", "Health check endpoint", 30, 40),
                ("get_users", "api.py", "Get users endpoint", 50, 65),
                ("User", "models.py", "User data model", 1, 30),
            ]

            for (
                func_name,
                file_name,
                description,
                start_line,
                end_line,
            ) in functions_data:
                func_query = f"""
                MATCH (f:File {{name: '{file_name}'}})
                CREATE (fn:Function {{
                    id: '{file_name}:{func_name}',
                    name: '{func_name}',
                    description: '{description}',
                    start_line: {start_line},
                    end_line: {end_line},
                    complexity: {(end_line - start_line) // 5 + 1},
                    created_at: datetime()
                }})
                CREATE (f)-[:CONTAINS]->(fn)
                RETURN fn
                """
                await client.execute_query(func_query)

            # 建立關係
            click.echo("🔗 建立示範關係...")
            relationships = [
                ("main.py:main", "config.py:get_config", "CALLS"),
                ("main.py:main", "database.py:connect_db", "CALLS"),
                ("api.py:get_users", "models.py:User", "USES"),
                ("api.py:health_check", "database.py:connect_db", "CALLS"),
            ]

            for source, target, rel_type in relationships:
                rel_query = f"""
                MATCH (source:Function {{id: '{source}'}}), (target:Function {{id: '{target}'}})
                CREATE (source)-[:{rel_type}]->(target)
                """
                await client.execute_query(rel_query)

            # 檢查結果
            click.echo("\n📊 驗證載入結果...")
            stats_query = """
            MATCH (p:Project) WITH count(p) as projects
            MATCH (f:File) WITH projects, count(f) as files
            MATCH (fn:Function) WITH projects, files, count(fn) as functions
            MATCH ()-[r]->() WITH projects, files, functions, count(r) as relationships
            RETURN projects, files, functions, relationships
            """
            result = await client.execute_query(stats_query)

            if not result.is_empty:
                stats = result.data[0]
                click.echo("✅ 載入完成!")
                click.echo(f"   - 專案: {stats['projects']}")
                click.echo(f"   - 文件: {stats['files']}")
                click.echo(f"   - 函數: {stats['functions']}")
                click.echo(f"   - 關係: {stats['relationships']}")

            # 提供試用建議
            click.echo("\n🎯 試用建議:")
            click.echo("   1. 執行搜索: mnemo search 'database connection'")
            click.echo("   2. 查看專案狀態: mnemo atlassian status")
            click.echo("   3. 測試 API: curl http://localhost:8000/health")

            await client.disconnect()

        except Exception as e:
            click.echo(f"❌ 示範資料載入失敗: {e}")

    asyncio.run(run_seeding())


@cli.command("search")
@click.argument("query")
@click.option("--top-k", default=5, help="返回結果數量")
@click.option(
    "--format",
    "output_format",
    default="table",
    type=click.Choice(["table", "json"]),
    help="輸出格式",
)
def search(query: str, top_k: int, output_format: str):
    """搜索知識圖譜"""
    click.echo(f"🔍 搜索: {query}")

    async def run_search():
        try:
            settings = get_settings()
            db_config = settings.database.to_connection_config()
            client = FalkorDBDriver(db_config)
            await client.connect()

            # 簡單的文本搜索查詢
            search_query = f"""
            MATCH (n)
            WHERE n.name CONTAINS '{query}' OR n.description CONTAINS '{query}'
            RETURN n.id as id, n.name as name, n.description as description, labels(n) as type
            LIMIT {top_k}
            """

            result = await client.execute_query(search_query)

            if result.is_empty:
                click.echo("📭 未找到相關結果")
                click.echo("提示: 可以先執行 'mnemo seed' 載入示範資料")
            else:
                click.echo(f"📊 找到 {result.count} 個結果:")

                if output_format == "json":
                    import json

                    click.echo(json.dumps(result.data, indent=2, ensure_ascii=False))
                else:
                    from tabulate import tabulate

                    headers = ["ID", "名稱", "描述", "類型"]
                    rows = []
                    for row in result.data:
                        rows.append(
                            [
                                row.get("id", ""),
                                row.get("name", ""),
                                row.get("description", ""),
                                ", ".join(row.get("type", [])),
                            ]
                        )
                    click.echo(tabulate(rows, headers=headers, tablefmt="grid"))

            await client.disconnect()

        except Exception as e:
            click.echo(f"❌ 搜索失敗: {e}")

    asyncio.run(run_search())


@cli.command("pr-check")
@click.option("--target-branch", default="main", help="目標分支名稱")
@click.option("--config", "config_path", help="配置檔案路徑")
@click.option(
    "--format",
    "format_type",
    type=click.Choice(["human", "json"]),
    default="human",
    help="輸出格式",
)
@click.option(
    "--severity-threshold",
    type=click.Choice(["error", "warning", "info"]),
    default="error",
    help="失敗的嚴重程度閾值",
)
@click.pass_context
def pr_check_command(
    ctx, target_branch: str, config_path: str, format_type: str, severity_threshold: str
):
    """檢查 PR 中的程式碼約束違規"""
    click.echo("🔍 程式碼治理檢查")
    click.echo(f"   - 目標分支: {target_branch}")
    click.echo(f"   - 輸出格式: {format_type}")
    click.echo(f"   - 嚴重程度: {severity_threshold}")

    if config_path:
        click.echo(f"   - 配置檔案: {config_path}")

    try:
        # 導入治理模組
        from .governance import GovernanceCLI

        cli_instance = GovernanceCLI()
        exit_code = asyncio.run(
            cli_instance.pr_check(
                target_branch=target_branch,
                config_path=config_path,
                format_type=format_type,
                severity_threshold=severity_threshold,
            )
        )

        if exit_code != 0:
            click.echo("❌ 程式碼檢查發現問題", err=True)
            ctx.exit(exit_code)
        else:
            click.echo("✅ 程式碼檢查通過")

    except ImportError as e:
        click.echo(f"❌ 治理模組未安裝: {e}", err=True)
        click.echo("請確保已安裝完整的開發依賴", err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(f"❌ 程式碼檢查失敗: {e}", err=True)
        ctx.exit(1)


@atlassian.command()
@click.argument("jql_query")
@click.option("--project", "-p", help="專案過濾器")
@click.option("--max-results", "-m", default=100, help="最大結果數量")
@click.option("--no-relationships", is_flag=True, help="不包含關聯關係")
def extract_jira(
    jql_query: str, project: Optional[str], max_results: int, no_relationships: bool
):
    """提取 Jira Issues 到知識圖譜"""
    click.echo(f"🎯 開始提取 Jira Issues: {jql_query}")

    if project:
        click.echo(f"   - 專案過濾: {project}")
    click.echo(f"   - 最大結果: {max_results}")
    click.echo(f"   - 包含關係: {'否' if no_relationships else '是'}")

    async def run_extraction():
        try:
            settings = get_settings()

            from ..ecl.atlassian_pipeline import AtlassianECLPipeline

            async with AtlassianECLPipeline(settings) as pipeline:
                result = await pipeline.extract_and_load_jira_issues(
                    jql_query=jql_query,
                    project_filter=project,
                    max_results=max_results,
                    include_relationships=not no_relationships,
                )

                if result.extraction_success:
                    click.echo("✅ 提取成功!")
                    click.echo(f"   - 實體數量: {result.entities_extracted}")
                    click.echo(f"   - 關係數量: {result.relationships_extracted}")

                    if result.load_result:
                        click.echo(
                            f"   - Issues 載入: {result.load_result.jira_issues_loaded}"
                        )
                        click.echo(
                            f"   - 關係載入: {result.load_result.relationships_loaded}"
                        )
                        click.echo(
                            f"   - 處理時間: {result.load_result.processing_time_ms}ms"
                        )

                        if result.load_result.errors:
                            click.echo("⚠️  載入警告:")
                            for error in result.load_result.errors:
                                click.echo(f"   - {error}")
                else:
                    click.echo("❌ 提取失敗:")
                    for error in result.errors:
                        click.echo(f"   - {error}")

        except Exception as e:
            click.echo(f"❌ 提取過程發生錯誤: {e}")

    asyncio.run(run_extraction())


@atlassian.command()
@click.argument("search_query")
@click.option("--space", "-s", help="空間過濾器")
@click.option("--max-results", "-m", default=100, help="最大結果數量")
@click.option("--no-relationships", is_flag=True, help="不包含關聯關係")
def extract_confluence(
    search_query: str, space: Optional[str], max_results: int, no_relationships: bool
):
    """提取 Confluence Pages 到知識圖譜"""
    click.echo(f"📄 開始提取 Confluence Pages: {search_query}")

    if space:
        click.echo(f"   - 空間過濾: {space}")
    click.echo(f"   - 最大結果: {max_results}")
    click.echo(f"   - 包含關係: {'否' if no_relationships else '是'}")

    async def run_extraction():
        try:
            settings = get_settings()

            from ..ecl.atlassian_pipeline import AtlassianECLPipeline

            async with AtlassianECLPipeline(settings) as pipeline:
                result = await pipeline.extract_and_load_confluence_pages(
                    query=search_query,
                    space_filter=space,
                    max_results=max_results,
                    include_relationships=not no_relationships,
                )

                if result.extraction_success:
                    click.echo("✅ 提取成功!")
                    click.echo(f"   - 實體數量: {result.entities_extracted}")
                    click.echo(f"   - 關係數量: {result.relationships_extracted}")

                    if result.load_result:
                        click.echo(
                            f"   - Pages 載入: "
                            f"{result.load_result.confluence_pages_loaded}"
                        )
                        click.echo(
                            f"   - 關係載入: {result.load_result.relationships_loaded}"
                        )
                        click.echo(
                            f"   - 處理時間: {result.load_result.processing_time_ms}ms"
                        )

                        if result.load_result.errors:
                            click.echo("⚠️  載入警告:")
                            for error in result.load_result.errors:
                                click.echo(f"   - {error}")
                else:
                    click.echo("❌ 提取失敗:")
                    for error in result.errors:
                        click.echo(f"   - {error}")

        except Exception as e:
            click.echo(f"❌ 提取過程發生錯誤: {e}")

    asyncio.run(run_extraction())


@atlassian.command()
def status():
    """檢查 Atlassian 管線狀態"""
    click.echo("📊 檢查 Atlassian 管線狀態")

    async def check_status():
        try:
            settings = get_settings()

            from ..ecl.atlassian_pipeline import AtlassianECLPipeline

            async with AtlassianECLPipeline(settings) as pipeline:
                status = await pipeline.get_pipeline_status()

                click.echo(
                    f"   - 資料庫連接: "
                    f"{'✅ 正常' if status.get('database_connected') else '❌ 異常'}"
                )

                if "statistics" in status:
                    stats = status["statistics"]
                    click.echo(f"   - Jira Issues: {stats.get('jira_issues', 0)}")
                    click.echo(
                        f"   - Confluence Pages: {stats.get('confluence_pages', 0)}"
                    )
                    click.echo(f"   - Projects: {stats.get('jira_projects', 0)}")
                    click.echo(f"   - Spaces: {stats.get('confluence_spaces', 0)}")
                    click.echo(f"   - 關係: {stats.get('relationships', 0)}")

                if "components" in status:
                    components = status["components"]
                    click.echo("   - 組件狀態:")
                    for comp, state in components.items():
                        status_icon = "✅" if state == "ready" else "❌"
                        click.echo(f"     • {comp}: {status_icon} {state}")

                if "error" in status:
                    click.echo(f"❌ 錯誤: {status['error']}")

        except Exception as e:
            click.echo(f"❌ 狀態檢查失敗: {e}")

    asyncio.run(check_status())


@atlassian.command()
@click.option("--source", "-s", help="指定要清除的資料源")
@click.option("--confirm", is_flag=True, help="確認清除操作")
def clear(source: Optional[str], confirm: bool):
    """清除 Atlassian 知識圖譜資料"""
    if not confirm:
        click.echo("⚠️  此操作將清除 Atlassian 知識圖譜資料")
        click.echo("請使用 --confirm 參數確認操作")
        return

    click.echo("🗑️  開始清除 Atlassian 資料")
    if source:
        click.echo(f"   - 資料源: {source}")
    else:
        click.echo("   - 範圍: 全部")

    async def run_clear():
        try:
            settings = get_settings()

            from ..ecl.atlassian_pipeline import AtlassianECLPipeline

            async with AtlassianECLPipeline(settings) as pipeline:
                await pipeline.clear_data(source)
                click.echo("✅ 清除完成!")

        except Exception as e:
            click.echo(f"❌ 清除失敗: {e}")

    asyncio.run(run_clear())


def main():
    """CLI 主入口點"""
    cli()


if __name__ == "__main__":
    main()
