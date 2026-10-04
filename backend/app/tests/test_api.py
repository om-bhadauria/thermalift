"""
Tests for THERMALIFT FastAPI API endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_endpoint_exists(self, client):
        """Test health endpoint returns 200."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
    
    def test_health_response_structure(self, client):
        """Test health response has expected fields."""
        response = client.get("/api/v1/health")
        data = response.json()
        
        assert "status" in data
        assert "service" in data
        assert "data_policy" in data
        assert data["status"] == "ok"
        assert data["service"] == "THERMALIFT"
        assert data["data_policy"] == "SYNTHETIC/DEMO"
    
    def test_health_no_stack_trace(self, client):
        """Test health endpoint doesn't expose internal details."""
        response = client.get("/api/v1/health")
        data = response.json()
        # Should not have traceback or internal paths
        assert "traceback" not in str(data).lower()
        assert "error" not in str(data).lower()


class TestSimulationEndpoint:
    """Test simulation endpoint."""
    
    def test_simulation_endpoint_exists(self, client):
        """Test simulation endpoint returns 200 for valid input."""
        request_data = {
            "well_id": "BW-001",
            "css_params": {
                "steam_rate_m3_d": 200,
                "steam_quality": 0.8,
                "injection_days": 10,
                "soak_days": 5,
                "production_days": 90
            },
            "srp_params": {
                "spm": 5.0,
                "stroke_length_m": 3.0,
                "vfd_frequency_hz": 40.0
            },
            "day_in_cycle": 5.0,
            "cycle_num": 1,
            "wellhead_pressure_kpa": 500.0
        }
        
        response = client.post("/api/v1/simulation", json=request_data)
        assert response.status_code == 200
    
    def test_simulation_response_structure(self, client):
        """Test simulation response has all expected fields."""
        request_data = {
            "well_id": "BW-001",
            "css_params": {
                "steam_rate_m3_d": 200,
                "steam_quality": 0.8,
                "injection_days": 10,
                "soak_days": 5,
                "production_days": 90
            },
            "srp_params": {
                "spm": 5.0,
                "stroke_length_m": 3.0,
                "vfd_frequency_hz": 40.0
            }
        }
        
        response = client.post("/api/v1/simulation", json=request_data)
        data = response.json()
        
        expected_fields = [
            "well_id", "timestamp", "temperature_c", "viscosity_cp",
            "production_rate_stb_d", "steam_rate_m3_d", "steam_pressure_kpa",
            "css_cycle", "srp_spm", "stroke_length_m", "pump_load_kn",
            "fillage", "pump_efficiency", "vfd_frequency_hz",
            "rod_float_risk", "impact_loading_risk", "data_source", "disclaimer"
        ]
        
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
    
    def test_simulation_invalid_well_id(self, client):
        """Test simulation with invalid well_id returns 404."""
        request_data = {
            "well_id": "INVALID-WELL",
            "css_params": {
                "steam_rate_m3_d": 200,
                "steam_quality": 0.8,
                "injection_days": 10,
                "soak_days": 5,
                "production_days": 90
            },
            "srp_params": {
                "spm": 5.0,
                "stroke_length_m": 3.0,
                "vfd_frequency_hz": 40.0
            }
        }
        
        response = client.post("/api/v1/simulation", json=request_data)
        assert response.status_code == 404
    
    def test_simulation_missing_srp_param(self, client):
        """Test simulation with missing SRP parameter returns 400."""
        request_data = {
            "well_id": "BW-001",
            "css_params": {
                "steam_rate_m3_d": 200,
                "steam_quality": 0.8,
                "injection_days": 10,
                "soak_days": 5,
                "production_days": 90
            },
            "srp_params": {
                "spm": 5.0,
                "stroke_length_m": 3.0
                # missing vfd_frequency_hz
            }
        }
        
        response = client.post("/api/v1/simulation", json=request_data)
        assert response.status_code == 400
    
    def test_simulation_disclaimer_present(self, client):
        """Test simulation response includes disclaimer."""
        request_data = {
            "well_id": "BW-001",
            "css_params": {"steam_rate_m3_d": 200, "steam_quality": 0.8, "injection_days": 10, "soak_days": 5, "production_days": 90},
            "srp_params": {"spm": 5.0, "stroke_length_m": 3.0, "vfd_frequency_hz": 40.0}
        }
        
        response = client.post("/api/v1/simulation", json=request_data)
        data = response.json()
        
        assert "disclaimer" in data
        assert "synthetic" in data["disclaimer"].lower()
        assert "demo" in data["disclaimer"].lower()
    
    def test_simulation_no_stack_trace(self, client):
        """Test simulation error doesn't expose stack trace."""
        request_data = {
            "well_id": "INVALID",
            "css_params": {},
            "srp_params": {}
        }
        
        response = client.post("/api/v1/simulation", json=request_data)
        assert response.status_code in [400, 404, 422]
        data = response.json()
        # Should not have traceback
        assert "traceback" not in str(data).lower()
    
    def test_list_wells_endpoint(self, client):
        """Test list wells endpoint."""
        response = client.get("/api/v1/simulation/wells")
        assert response.status_code == 200
        data = response.json()
        assert "wells" in data
        assert len(data["wells"]) == 5
        assert data["data_source"] == "SYNTHETIC"


class TestPredictionEndpoint:
    """Test ML prediction endpoint."""
    
    def test_prediction_endpoint_exists(self, client):
        """Test prediction endpoint returns 200 for valid input."""
        request_data = {
            "well_id": "BW-001",
            "state": {
                "temperature_c": 120,
                "viscosity_cp": 5000,
                "steam_rate_m3_d": 200,
                "steam_pressure_kpa": 4500,
                "css_cycle": 1,
                "srp_spm": 5.0,
                "stroke_length_m": 3.0,
                "pump_load_kn": 150,
                "fillage": 0.85,
                "pump_efficiency": 0.88,
                "vfd_frequency_hz": 40.0
            }
        }
        
        response = client.post("/api/v1/prediction", json=request_data)
        assert response.status_code == 200
    
    def test_prediction_response_structure(self, client):
        """Test prediction response structure."""
        request_data = {
            "well_id": "BW-001",
            "state": {
                "temperature_c": 120,
                "viscosity_cp": 5000,
                "steam_rate_m3_d": 200,
                "steam_pressure_kpa": 4500,
                "css_cycle": 1,
                "srp_spm": 5.0,
                "stroke_length_m": 3.0,
                "pump_load_kn": 150,
                "fillage": 0.85,
                "pump_efficiency": 0.88,
                "vfd_frequency_hz": 40.0
            }
        }
        
        response = client.post("/api/v1/prediction", json=request_data)
        if response.status_code == 200:
            data = response.json()
            
            assert "well_id" in data
            assert "predicted_production_stb_d" in data
            assert "predicted_rod_float_risk" in data
            assert "predicted_impact_loading_risk" in data
            assert "model_info" in data
            assert "data_source" in data
            assert "disclaimer" in data
    
    def test_prediction_invalid_well_id(self, client):
        """Test prediction with invalid well_id returns 404."""
        request_data = {
            "well_id": "INVALID",
            "state": {"temperature_c": 120}
        }
        
        response = client.post("/api/v1/prediction", json=request_data)
        assert response.status_code == 404
    
    def test_prediction_disclaimer_present(self, client):
        """Test prediction response includes disclaimer."""
        request_data = {
            "well_id": "BW-001",
            "state": {
                "temperature_c": 120,
                "viscosity_cp": 5000,
                "steam_rate_m3_d": 200,
                "steam_pressure_kpa": 4500,
                "css_cycle": 1,
                "srp_spm": 5.0,
                "stroke_length_m": 3.0,
                "pump_load_kn": 150,
                "fillage": 0.85,
                "pump_efficiency": 0.88,
                "vfd_frequency_hz": 40.0
            }
        }
        
        response = client.post("/api/v1/prediction", json=request_data)
        if response.status_code == 200:
            data = response.json()
            assert "disclaimer" in data
            assert "synthetic" in data["disclaimer"].lower()
            assert "demo" in data["disclaimer"].lower()
    
    def test_model_status_endpoint(self, client):
        """Test model status endpoint."""
        response = client.get("/api/v1/prediction/models/status")
        assert response.status_code == 200
        data = response.json()
        assert "initialized" in data
        assert "data_source" in data


class TestOptimizationEndpoint:
    """Test optimization endpoint."""
    
    def test_optimization_endpoint_exists(self, client):
        """Test optimization endpoint returns 200 for valid input."""
        request_data = {
            "well_id": "BW-001",
            "grid_resolution": 1,
            "day_in_cycle": 5.0,
            "cycle_num": 1,
            "wellhead_pressure_kpa": 500.0,
            "random_seed": 42
        }
        
        response = client.post("/api/v1/optimization", json=request_data)
        assert response.status_code == 200
    
    def test_optimization_response_structure(self, client):
        """Test optimization response structure."""
        request_data = {
            "well_id": "BW-001",
            "grid_resolution": 1,
            "day_in_cycle": 5.0,
            "cycle_num": 1,
            "wellhead_pressure_kpa": 500.0,
            "random_seed": 42
        }
        
        response = client.post("/api/v1/optimization", json=request_data)
        if response.status_code == 200:
            data = response.json()
            
            assert "well_id" in data
            assert "best_candidate" in data
            assert "baseline_comparison" in data
            assert "recommendation" in data
            assert "total_evaluated" in data
            assert "feasible_count" in data
            assert "execution_time_seconds" in data
            assert "data_source" in data
            assert "disclaimer" in data
    
    def test_optimization_invalid_well_id(self, client):
        """Test optimization with invalid well_id returns 404."""
        request_data = {
            "well_id": "INVALID",
            "grid_resolution": 1
        }
        
        response = client.post("/api/v1/optimization", json=request_data)
        assert response.status_code == 404
    
    def test_optimization_invalid_grid_resolution(self, client):
        """Test optimization with invalid grid resolution returns 422."""
        request_data = {
            "well_id": "BW-001",
            "grid_resolution": 10  # > 5 max
        }
        
        response = client.post("/api/v1/optimization", json=request_data)
        assert response.status_code == 422
    
    def test_optimization_disclaimer_present(self, client):
        """Test optimization response includes disclaimer."""
        request_data = {
            "well_id": "BW-001",
            "grid_resolution": 1,
            "random_seed": 42
        }
        
        response = client.post("/api/v1/optimization", json=request_data)
        if response.status_code == 200:
            data = response.json()
            assert "disclaimer" in data
            assert "synthetic" in data["disclaimer"].lower()
            assert "demo" in data["disclaimer"].lower()
    
    def test_default_constraints_endpoint(self, client):
        """Test default constraints endpoint."""
        response = client.get("/api/v1/optimization/constraints/default")
        assert response.status_code == 200
        data = response.json()
        assert "constraints" in data
        assert "description" in data
    
    def test_default_weights_endpoint(self, client):
        """Test default weights endpoint."""
        response = client.get("/api/v1/optimization/weights/default")
        assert response.status_code == 200
        data = response.json()
        assert "weights" in data
        assert "description" in data


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns service info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        
        assert "service" in data
        assert "version" in data
        assert "data_policy" in data
        assert data["service"] == "THERMALIFT"
        assert data["data_policy"] == "SYNTHETIC/DEMO"


class TestCORS:
    """Test CORS configuration."""
    
    def test_cors_preflight_allowed_origin(self, client):
        """Test CORS preflight request with allowed origin."""
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "https://thermalift.netlify.app",
                "Access-Control-Request-Method": "GET",
            }
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "https://thermalift.netlify.app"
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
    
    def test_cors_preflight_localhost_origin(self, client):
        """Test CORS preflight request with localhost origin."""
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            }
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    
    def test_cors_actual_request_allowed_origin(self, client):
        """Test actual GET request with allowed origin returns CORS headers."""
        response = client.get(
            "/api/v1/health",
            headers={"Origin": "https://thermalift.netlify.app"}
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "https://thermalift.netlify.app"
    
    def test_cors_actual_request_localhost_origin(self, client):
        """Test actual GET request with localhost origin returns CORS headers."""
        response = client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:5173"}
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    
    def test_cors_simulation_endpoint(self, client):
        """Test CORS headers on simulation POST endpoint."""
        response = client.options(
            "/api/v1/simulation",
            headers={
                "Origin": "https://thermalift.netlify.app",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            }
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "https://thermalift.netlify.app"
    
    def test_cors_optimization_endpoint(self, client):
        """Test CORS headers on optimization POST endpoint."""
        response = client.options(
            "/api/v1/optimization",
            headers={
                "Origin": "https://thermalift.netlify.app",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            }
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "https://thermalift.netlify.app"
    
    def test_cors_credentials_allowed(self, client):
        """Test that credentials are allowed for allowed origins."""
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "https://thermalift.netlify.app",
                "Access-Control-Request-Method": "GET",
            }
        )
        assert response.headers.get("access-control-allow-credentials") == "true"


class TestAPIDocs:
    """Test API documentation accessibility."""
    
    def test_docs_endpoint(self, client):
        """Test /docs endpoint is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_openapi_endpoint(self, client):
        """Test /openapi.json endpoint is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "THERMALIFT"


class TestEndToEndFlow:
    """Test basic end-to-end API flow."""
    
    def test_simulation_to_optimization_flow(self, client):
        """Test running simulation then optimization."""
        # Run simulation
        sim_request = {
            "well_id": "BW-001",
            "css_params": {"steam_rate_m3_d": 200, "steam_quality": 0.8, "injection_days": 10, "soak_days": 5, "production_days": 90},
            "srp_params": {"spm": 5.0, "stroke_length_m": 3.0, "vfd_frequency_hz": 40.0}
        }
        
        sim_response = client.post("/api/v1/simulation", json=sim_request)
        assert sim_response.status_code == 200
        
        # Run optimization
        opt_request = {
            "well_id": "BW-001",
            "grid_resolution": 1,
            "random_seed": 42
        }
        
        opt_response = client.post("/api/v1/optimization", json=opt_request)
        assert opt_response.status_code == 200
        
        opt_data = opt_response.json()
        assert opt_data["total_evaluated"] > 0
        assert "disclaimer" in opt_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])