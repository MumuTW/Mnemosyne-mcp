"""
Mnemosyne MCP CLI 主入口

提供命令行工具的基本功能。
"""

import asyncio
from typing import Optional

import click

from ..core.config import get_settings, validate_config
from ..core.logging import setup_logging
from ..drivers.falkordb_driver import FalkorDBDriver


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
                            f"   - Pages 載入: {result.load_result.confluence_pages_loaded}"
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
                    f"   - 資料庫連接: {'✅ 正常' if status.get('database_connected') else '❌ 異常'}"
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
