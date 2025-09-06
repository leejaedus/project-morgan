"""
Morgan - CLI Interface

Beautiful command-line interface for the Morgan Slack activity manager.
"""

import asyncio
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Confirm, IntPrompt

from models import Priority, TodoList
from morgan import MorganOrchestrator

# Initialize CLI app
app = typer.Typer(
    name="morgan",
    help="🤖 Morgan - AI-powered smart Slack activity manager",
    add_completion=False
)

# Rich console for beautiful output
console = Console()

# Global orchestrator instance
morgan: Optional[MorganOrchestrator] = None


def get_morgan() -> MorganOrchestrator:
    """Get or create Morgan orchestrator instance"""
    global morgan
    if morgan is None:
        morgan = MorganOrchestrator()
    return morgan


def check_environment() -> bool:
    """Check if required environment variables are set"""
    required_vars = ["SLACK_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        console.print("❌ [red]Missing required environment variables:[/red]")
        for var in missing_vars:
            console.print(f"   • {var}")
        console.print("\n💡 Create a .env file or set these environment variables.")
        console.print("   Example: export SLACK_TOKEN=xoxp-your-token")
        return False
    
    return True


def display_todo_list(todo_list: TodoList) -> None:
    """Display todo list in a beautiful table"""
    if not todo_list.items:
        console.print("📝 할일이 없습니다! 🎉")
        return
    
    # Create table
    table = Table(title=f"📋 {todo_list.title}")
    table.add_column("우선순위", style="cyan", width=8)
    table.add_column("할일", style="white", width=40)
    table.add_column("발신자", style="green", width=15)
    table.add_column("채널", style="yellow", width=15)
    table.add_column("권장 처리시간", style="magenta", width=20)
    
    # Group by priority
    priority_colors = {
        Priority.URGENT: "red",
        Priority.HIGH: "orange3",
        Priority.MEDIUM: "yellow",
        Priority.LOW: "green"
    }
    
    priority_icons = {
        Priority.URGENT: "🔥",
        Priority.HIGH: "⚡",
        Priority.MEDIUM: "📌",
        Priority.LOW: "📝"
    }
    
    for todo in todo_list.items:
        priority_text = Text(
            f"{priority_icons[todo.priority]} {todo.priority.value.upper()}",
            style=priority_colors[todo.priority]
        )
        
        table.add_row(
            priority_text,
            todo.title,
            todo.source_message.username,
            f"#{todo.source_message.channel_name}",
            todo.priority_score.recommended_action_time
        )
    
    console.print(table)
    
    # Summary stats
    stats = Panel(
        f"📊 총 {todo_list.total_items}개 할일 | "
        f"🔥 긴급 {len(todo_list.get_by_priority(Priority.URGENT))}개 | "
        f"⚡ 높음 {len(todo_list.get_by_priority(Priority.HIGH))}개 | "
        f"📌 보통 {len(todo_list.get_by_priority(Priority.MEDIUM))}개 | "
        f"📝 낮음 {len(todo_list.get_by_priority(Priority.LOW))}개",
        title="요약",
        border_style="blue"
    )
    console.print(stats)


def display_todo_details(todo_list: TodoList, index: int) -> None:
    """Display detailed information for a specific todo"""
    if index < 1 or index > len(todo_list.items):
        console.print("❌ 잘못된 할일 번호입니다.")
        return
    
    todo = todo_list.items[index - 1]
    
    # Create detailed panel
    details = f"""
🆔 ID: {todo.id}
📅 생성시간: {todo.created_at.strftime('%Y-%m-%d %H:%M:%S')}

📍 원본 메시지:
   👤 발신자: {todo.source_message.username}
   📍 채널: #{todo.source_message.channel_name}
   ⏰ 시간: {todo.source_message.timestamp.strftime('%Y-%m-%d %H:%M')}
   🔗 링크: {todo.source_message.permalink}

💬 메시지 내용:
{todo.source_message.text}

🤖 AI 분석:
   📝 작업 유형: {todo.ai_analysis.work_type}
   ⚡ 긴급도: {todo.ai_analysis.urgency_score:.2f}
   🧠 복잡도: {todo.ai_analysis.complexity}
   ⏱️ 예상 시간: {todo.ai_analysis.estimated_time_minutes}분
   😊 감정 톤: {todo.ai_analysis.emotional_tone}
   🤖 분석 모델: {todo.ai_analysis.model_used}

🎯 우선순위 분석:
   📊 최종 점수: {todo.priority_score.final_score:.3f}
   🔥 우선순위: {todo.priority.value.upper()}
   💡 근거: {todo.priority_score.reasoning}
   📅 권장 시간: {todo.priority_score.recommended_action_time}

🏷️ 태그: {', '.join(todo.tags)}
"""
    
    panel = Panel(
        details.strip(),
        title=f"📋 {todo.title}",
        border_style="green" if todo.priority in [Priority.LOW, Priority.MEDIUM] else "red"
    )
    
    console.print(panel)


@app.command()
def analyze(
    hours: int = typer.Option(24, "--hours", "-h", help="분석할 시간 범위 (시간)"),
    max_messages: int = typer.Option(100, "--max", "-m", help="처리할 최대 메시지 수"),
    save: bool = typer.Option(False, "--save", "-s", help="결과를 파일로 저장")
):
    """🔍 슬랙 활동을 분석하고 할일 목록을 생성합니다"""
    
    if not check_environment():
        raise typer.Exit(1)
    
    console.print("🤖 [bold blue]Morgan이 슬랙 활동을 분석합니다...[/bold blue]")
    
    # Show progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("분석 중...", total=None)
        
        # Run async analysis
        async def run_analysis():
            orchestrator = get_morgan()
            return await orchestrator.process_slack_activities(hours, max_messages)
        
        todo_list = asyncio.run(run_analysis())
        progress.update(task, description="완료!")
    
    # Display results
    console.print("\n" + "="*60)
    display_todo_list(todo_list)
    
    if todo_list.items:
        console.print(f"\n💡 [dim]자세한 내용을 보려면: [bold]morgan details [1-{len(todo_list.items)}][/bold][/dim]")
        console.print("💡 [dim]피드백을 주려면: [bold]morgan feedback <할일번호> <만족도1-5>[/bold][/dim]")
    
    # Save if requested
    if save and todo_list.items:
        filename = f"morgan_todos_{todo_list.created_at.strftime('%Y%m%d_%H%M')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"{todo_list.title}\n")
            f.write("="*60 + "\n\n")
            
            for i, todo in enumerate(todo_list.items, 1):
                f.write(f"{i}. [{todo.priority.value.upper()}] {todo.title}\n")
                f.write(f"   발신자: {todo.source_message.username}\n")
                f.write(f"   채널: #{todo.source_message.channel_name}\n")
                f.write(f"   권장 처리: {todo.priority_score.recommended_action_time}\n")
                f.write(f"   내용: {todo.source_message.text}\n\n")
        
        console.print(f"💾 결과가 [green]{filename}[/green]에 저장되었습니다.")


@app.command()
def details(
    number: int = typer.Argument(..., help="할일 번호"),
    hours: int = typer.Option(24, "--hours", "-h", help="분석할 시간 범위 (시간)")
):
    """📖 특정 할일의 상세 정보를 표시합니다"""
    
    if not check_environment():
        raise typer.Exit(1)
    
    # Re-analyze to get current todo list (in real app, this would be cached)
    async def get_todo_list():
        orchestrator = get_morgan()
        return await orchestrator.process_slack_activities(hours, max_messages=50)
    
    with console.status("할일 목록을 불러오는 중..."):
        todo_list = asyncio.run(get_todo_list())
    
    display_todo_details(todo_list, number)


@app.command()
def feedback(
    todo_number: int = typer.Argument(..., help="할일 번호"),
    satisfaction: int = typer.Argument(..., help="만족도 (1-5)"),
    comment: Optional[str] = typer.Option(None, "--comment", "-c", help="추가 의견")
):
    """📝 할일에 대한 피드백을 제공합니다 (학습용)"""
    
    if satisfaction < 1 or satisfaction > 5:
        console.print("❌ 만족도는 1-5 사이의 숫자여야 합니다.")
        raise typer.Exit(1)
    
    orchestrator = get_morgan()
    
    # For demo purposes, create a dummy todo_id
    todo_id = f"todo_{todo_number}"
    
    feedback = orchestrator.collect_feedback(
        todo_id=todo_id,
        satisfaction=satisfaction,
        feedback_text=comment
    )
    
    console.print(f"✅ 피드백이 기록되었습니다!")
    console.print(f"   할일 번호: {todo_number}")
    console.print(f"   만족도: {satisfaction}/5 {'⭐' * satisfaction}")
    if comment:
        console.print(f"   의견: {comment}")
    
    console.print("\n🧠 Morgan이 당신의 피드백으로부터 학습하고 있습니다...")


@app.command()
def config():
    """⚙️ 설정을 확인하고 관리합니다"""
    
    console.print("⚙️ [bold]Morgan 설정[/bold]\n")
    
    # Check environment variables
    env_vars = {
        "SLACK_TOKEN": "슬랙 토큰",
        "OPENAI_API_KEY": "OpenAI API 키", 
        "ANTHROPIC_API_KEY": "Anthropic API 키"
    }
    
    table = Table(title="환경 변수")
    table.add_column("변수명", style="cyan")
    table.add_column("설명", style="white")
    table.add_column("상태", style="green")
    
    for var, desc in env_vars.items():
        value = os.getenv(var)
        status = "✅ 설정됨" if value else "❌ 없음"
        if value:
            # Show partial value for security
            display_value = value[:10] + "..." if len(value) > 10 else value
            status += f" ({display_value})"
        
        table.add_row(var, desc, status)
    
    console.print(table)
    
    # Config file info
    env_file = Path(".env")
    if env_file.exists():
        console.print(f"\n💡 설정 파일: [green].env[/green] 파일이 존재합니다.")
    else:
        console.print(f"\n💡 설정 파일: [yellow].env[/yellow] 파일이 없습니다.")
        console.print("   .env.example 파일을 복사해서 .env로 이름을 변경하고 토큰을 입력하세요.")


@app.command()
def stats():
    """📊 사용 통계를 표시합니다"""
    
    if not check_environment():
        raise typer.Exit(1)
    
    orchestrator = get_morgan()
    stats = orchestrator.get_summary_stats()
    
    console.print("📊 [bold]Morgan 사용 통계[/bold]\n")
    
    ai_stats = stats["ai_usage"]
    
    # AI Usage table
    table = Table(title="AI 사용량")
    table.add_column("항목", style="cyan")
    table.add_column("값", style="white")
    
    table.add_row("OpenAI 호출", f"{ai_stats['openai_calls']}회")
    table.add_row("Claude 호출", f"{ai_stats['claude_calls']}회")
    table.add_row("총 호출", f"{ai_stats['total_calls']}회")
    table.add_row("예상 비용", f"${ai_stats['estimated_cost_usd']}")
    table.add_row("OpenAI 비율", f"{ai_stats['openai_percentage']}%")
    table.add_row("Claude 비율", f"{ai_stats['claude_percentage']}%")
    
    console.print(table)
    
    console.print(f"\n👤 학습된 사용자 패턴: {stats['user_patterns_count']}개")
    console.print(f"⏰ 마지막 처리: {stats['last_processed']}")


@app.callback()
def main():
    """
    🤖 Morgan - AI 기반 스마트 슬랙 활동 관리자
    
    슬랙 활동을 분석하고 똑똑한 할일 목록을 생성합니다.
    """
    pass


if __name__ == "__main__":
    app()