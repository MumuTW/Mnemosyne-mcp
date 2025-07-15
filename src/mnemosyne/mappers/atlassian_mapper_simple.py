"""
Atlassian 數據映射器 - 簡化版本

將 Jira Issue 和 Confluence 頁面數據映射為知識圖譜節點。
"""

from typing import List, Optional, Tuple

import structlog

from ..clients.atlassian import ConfluencePage, JiraIssue
from ..schemas.core import BaseEntity, EntityType
from ..schemas.relationships import BaseRelationship, RelationshipType

logger = structlog.get_logger(__name__)


class AtlassianMapper:
    """Atlassian 數據映射器"""

    @staticmethod
    def jira_issue_to_entity(issue: JiraIssue) -> BaseEntity:
        """將 Jira Issue 轉換為 Entity 節點"""
        extra = {
            "jira_key": issue.key,
            "jira_id": issue.id,
            "status": issue.status,
            "issue_type": "jira_issue",
            "source": "jira",
        }

        # 添加可選屬性
        if issue.description:
            extra["description"] = issue.description
        if issue.priority:
            extra["priority"] = issue.priority
        if issue.project:
            extra["project"] = issue.project
        if issue.assignee:
            extra["assignee"] = issue.assignee
        if issue.reporter:
            extra["reporter"] = issue.reporter
        if issue.created:
            extra["created_date"] = issue.created
        if issue.updated:
            extra["updated_date"] = issue.updated
        if issue.labels:
            extra["labels"] = issue.labels

        return BaseEntity(
            id=f"jira_issue_{issue.key}",
            entity_type=EntityType.ISSUE,
            name=issue.summary,
            extra=extra,
        )

    @staticmethod
    def confluence_page_to_entity(page: ConfluencePage) -> BaseEntity:
        """將 Confluence 頁面轉換為 Entity 節點"""
        extra = {
            "confluence_id": page.id,
            "title": page.title,
            "document_type": "confluence_page",
            "source": "confluence",
        }

        # 添加可選屬性
        if page.content:
            extra["content"] = page.content
        if page.space:
            extra["space"] = page.space
        if page.author:
            extra["author"] = page.author
        if page.created:
            extra["created_date"] = page.created
        if page.updated:
            extra["updated_date"] = page.updated
        if page.version:
            extra["version"] = page.version
        if page.url:
            extra["url"] = page.url

        return BaseEntity(
            id=f"confluence_page_{page.id}",
            entity_type=EntityType.DOCUMENT,
            name=page.title,
            extra=extra,
        )

    @staticmethod
    def create_project_relationship(
        issue_entity: BaseEntity, project_name: str
    ) -> Optional[BaseRelationship]:
        """創建 Issue 與 Project 的關係"""
        try:
            project_entity_id = f"jira_project_{project_name}"

            return BaseRelationship(
                id=f"rel_{issue_entity.id}_{project_entity_id}",
                source_id=issue_entity.id,
                target_id=project_entity_id,
                relationship_type=RelationshipType.BELONGS_TO,
                extra={
                    "relationship_type": "issue_to_project",
                    "project_name": project_name,
                },
            )
        except Exception as e:
            logger.error(
                "Failed to create project relationship",
                issue_entity_id=issue_entity.id,
                project_name=project_name,
                error=str(e),
            )
            return None

    @staticmethod
    def batch_map_jira_issues(
        issues: List[JiraIssue],
    ) -> Tuple[List[BaseEntity], List[BaseRelationship]]:
        """批次映射 Jira Issues 到實體和關係"""
        entities = []
        relationships = []

        for issue in issues:
            try:
                entity = AtlassianMapper.jira_issue_to_entity(issue)
                entities.append(entity)

                # 創建專案關係
                if issue.project:
                    project_rel = AtlassianMapper.create_project_relationship(
                        entity, issue.project
                    )
                    if project_rel:
                        relationships.append(project_rel)

            except Exception as e:
                logger.error(
                    "Failed to map Jira issue in batch",
                    issue_key=issue.key,
                    error=str(e),
                )
                continue

        return entities, relationships

    @staticmethod
    def create_space_relationship(
        page_entity: BaseEntity, space_name: str
    ) -> Optional[BaseRelationship]:
        """創建 Page 與 Space 的關係"""
        try:
            space_entity_id = f"confluence_space_{space_name}"

            return BaseRelationship(
                id=f"rel_{page_entity.id}_{space_entity_id}",
                source_id=page_entity.id,
                target_id=space_entity_id,
                relationship_type=RelationshipType.BELONGS_TO,
                extra={
                    "relationship_type": "page_to_space",
                    "space_name": space_name,
                },
            )
        except Exception as e:
            logger.error(
                "Failed to create space relationship",
                page_entity_id=page_entity.id,
                space_name=space_name,
                error=str(e),
            )
            return None

    @staticmethod
    def batch_map_confluence_pages(
        pages: List[ConfluencePage],
    ) -> Tuple[List[BaseEntity], List[BaseRelationship]]:
        """批次映射 Confluence 頁面到實體和關係"""
        entities = []
        relationships = []

        for page in pages:
            try:
                entity = AtlassianMapper.confluence_page_to_entity(page)
                entities.append(entity)

                # 創建空間關係
                if page.space:
                    space_rel = AtlassianMapper.create_space_relationship(
                        entity, page.space
                    )
                    if space_rel:
                        relationships.append(space_rel)

            except Exception as e:
                logger.error(
                    "Failed to map Confluence page in batch",
                    page_id=page.id,
                    error=str(e),
                )
                continue

        return entities, relationships
