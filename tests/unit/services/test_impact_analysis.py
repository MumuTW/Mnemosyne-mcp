"""
影響力分析服務單元測試
"""


class TestImpactAnalysisService:
    """影響力分析服務測試類別"""

    def test_risk_score_calculation(self):
        """測試風險評分計算"""

        def calculate_risk_score(callers_count, dependencies_count, coupling):
            risk_score = 0.0

            # 基於呼叫者數量的風險
            if callers_count > 20:
                risk_score += 0.4
            elif callers_count > 10:
                risk_score += 0.2

            # 基於依賴數量的風險
            if dependencies_count > 15:
                risk_score += 0.3
            elif dependencies_count > 8:
                risk_score += 0.15

            # 基於複雜度的風險
            if coupling > 25:
                risk_score += 0.3
            elif coupling > 15:
                risk_score += 0.15

            return min(risk_score, 1.0)

        # 測試低風險情況
        low_risk = calculate_risk_score(5, 3, 8)
        assert low_risk < 0.5

        # 測試高風險情況
        high_risk = calculate_risk_score(25, 20, 30)
        assert high_risk > 0.5

    def test_impact_node_creation(self):
        """測試影響節點建立"""

        def create_impact_node(node_id, node_type, name, impact_type):
            return {
                "node_id": node_id,
                "node_type": node_type,
                "name": name,
                "impact_type": impact_type,
                "risk_score": 0.7 if impact_type == "caller" else 0.4,
            }

        # 測試呼叫者節點
        caller_node = create_impact_node("caller1", "Function", "test_caller", "caller")
        assert caller_node["risk_score"] == 0.7
        assert caller_node["impact_type"] == "caller"

        # 測試依賴節點
        dep_node = create_impact_node(
            "dep1", "Function", "test_dependency", "dependency"
        )
        assert dep_node["risk_score"] == 0.4
        assert dep_node["impact_type"] == "dependency"

    def test_recommendation_generation(self):
        """測試建議生成"""

        def generate_recommendations(callers_count, dependencies_count, risk_score):
            recommendations = []

            if risk_score > 0.7:
                recommendations.append(
                    "Consider breaking this function into smaller parts"
                )
                recommendations.append("Implement comprehensive unit tests")

            if callers_count > 10:
                recommendations.append(
                    "Review all calling functions for breaking changes"
                )

            if dependencies_count > 10:
                recommendations.append("Analyze dependency chain for cascading effects")

            recommendations.append("Perform thorough integration testing")
            return recommendations

        # 測試高風險建議
        high_risk_recs = generate_recommendations(15, 12, 0.8)
        assert len(high_risk_recs) >= 4
        assert any("breaking" in rec.lower() for rec in high_risk_recs)

        # 測試低風險建議
        low_risk_recs = generate_recommendations(3, 2, 0.2)
        assert len(low_risk_recs) >= 1
        assert "integration testing" in low_risk_recs[-1].lower()
