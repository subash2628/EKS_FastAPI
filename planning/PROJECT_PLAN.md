# Project Plan: FastAPI + MySQL on EKS with GitOps & Observability

**Status:** Planning
**Last updated:** 2026-06-22
**Goal:** A real, production-grade app deployed on EKS with full CI/CD (GitHub Actions → ArgoCD) and observability (Prometheus/Grafana).

---

## 1. Project Summary

A FastAPI application with a built-in UI for querying a MySQL database. The database runs on **AWS RDS** (managed). The app is containerized, deployed to **EKS**, and kept in sync via **ArgoCD** (GitOps). **GitHub Actions** handles build/test/push and updates deployment manifests. **Prometheus + Grafana** provide metrics and dashboards.

---

## 2. Architecture

```
                    ┌─────────────────────┐
                    │   GitHub Repo        │
                    │  app/ k8s/ argocd/   │
                    └─────────┬────────────┘
                              │ push
                    ┌─────────▼────────────┐
                    │  GitHub Actions (CI) │
                    │  test → build → push │
                    │  to ECR → bump tag    │
                    │  in k8s manifest      │
                    └─────────┬────────────┘
                              │ git commit (new image tag)
                    ┌─────────▼────────────┐
                    │      ArgoCD (CD)      │
                    │  watches repo, syncs  │
                    └─────────┬────────────┘
                              │
                    ┌─────────▼────────────┐
                    │      EKS Cluster      │
                    │ ┌───────────────────┐ │
                    │ │ FastAPI Deployment│ │──────► RDS MySQL (private subnet)
                    │ │ Service + Ingress │ │
                    │ └───────────────────┘ │
                    │ ┌───────────────────┐ │
                    │ │ Prometheus +      │ │
                    │ │ Grafana           │ │
                    │ └───────────────────┘ │
                    └───────────────────────┘
```

**Key decisions made:**
| Decision | Choice | Why |
|---|---|---|
| Database | AWS RDS (MySQL 8.x) | Managed backups, patching, failover — lower ops burden for a "real" app |
| Cluster provisioning | AWS Web Console | Chosen approach for this project (see note below) |
| GitOps tool | ArgoCD | Auto-sync from git as source of truth |
| Metrics | Prometheus + Grafana (kube-prometheus-stack) | Industry standard, integrates with ArgoCD-managed deploys |

> **Note on console-provisioned infra:** Since EKS/VPC/RDS are created via the AWS console rather than Terraform, there's no IaC record of them. Recommended hygiene: keep a `infra/NOTES.md` documenting exact settings (VPC CIDR, subnet IDs, security group rules, instance types) so the cluster/DB could be recreated manually if needed. Migrating to Terraform later is a good future improvement, not a blocker now.

---

## 3. Repository Structure

```
.
├── app/
│   ├── main.py
│   ├── db.py
│   ├── models.py
│   ├── templates/            # UI (Jinja2) or static/ if using JS frontend
│   ├── requirements.txt
│   └── Dockerfile
├── k8s/
│   ├── fastapi/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── ingress.yaml
│   │   └── secret.yaml      # (or externalsecret.yaml if using ESO)
│   └── monitoring/
│       └── values.yaml      # kube-prometheus-stack helm values
├── argocd/
│   └── applications/
│       ├── fastapi-app.yaml
│       └── monitoring.yaml
├── infra/
│   └── NOTES.md             # manual AWS console setup documentation
├── .github/
│   └── workflows/
│       └── ci.yml
└── PROJECT_PLAN.md           # this file
```

---

## 4. Build Phases & Checklist

### Phase 0 — Local Dev
- [ ] Scaffold FastAPI app (`main.py`, routers, templates)
- [ ] SQLAlchemy models + connection layer
- [ ] Build a **safe** query interface (predefined filters/templates — avoid raw free-form SQL injection risk if UI lets users type queries)
- [ ] Local `docker-compose.yml` with MySQL for dev/testing
- [ ] `/health` endpoint
- [ ] `/metrics` endpoint via `prometheus-fastapi-instrumentator`
- [ ] Dockerfile (multi-stage build, slim base image)
- [ ] Basic tests (pytest)

### Phase 1 — AWS Networking & RDS
- [ ] Create/confirm VPC with public + private subnets, NAT gateway
- [ ] Create RDS MySQL instance in **private subnets**
- [ ] RDS security group: allow 3306 only from EKS node SG (set this up after Phase 2, or pre-create SG and attach later)
- [ ] Enable automated backups on RDS
- [ ] Store DB credentials in **AWS Secrets Manager**
- [ ] Document everything in `infra/NOTES.md`

### Phase 2 — EKS Cluster
- [ ] Create EKS cluster via console (same VPC as RDS)
- [ ] Create managed node group (start small, e.g. 2x t3.medium)
- [ ] Enable IAM OIDC provider (needed for IRSA)
- [ ] Configure `kubectl` access (update kubeconfig)
- [ ] Install EBS CSI driver (for any PVC needs, e.g. Prometheus storage)
- [ ] Install AWS Load Balancer Controller (for Ingress)
- [ ] Install metrics-server
- [ ] Verify connectivity: spin up a debug pod, confirm it can reach RDS endpoint on 3306

### Phase 3 — Manual Deploy (validate before automating)
- [ ] Push Docker image to ECR manually
- [ ] Create k8s Secret (or Secrets Manager sync) with DB credentials
- [ ] Apply Deployment + Service + Ingress manually
- [ ] Confirm app is reachable and successfully queries RDS
- [ ] Confirm `/metrics` endpoint is exposed correctly

### Phase 4 — ArgoCD (GitOps)
- [ ] Install ArgoCD on EKS
- [ ] Expose ArgoCD UI securely (Ingress + auth, not public LoadBalancer with defaults)
- [ ] Create `Application` manifest pointing to `k8s/fastapi/`
- [ ] Enable auto-sync + self-heal
- [ ] Confirm: manual `kubectl apply` is no longer needed; git is now source of truth

### Phase 5 — GitHub Actions CI
- [ ] Set up GitHub OIDC → AWS IAM role (no long-lived AWS keys in CI)
- [ ] Workflow: on push to `main`
  - [ ] Run tests/lint
  - [ ] Build Docker image
  - [ ] Push to ECR (tag with git SHA)
  - [ ] Update image tag in `k8s/fastapi/deployment.yaml` (via `yq`/`kustomize`)
  - [ ] Commit the manifest change back to repo
- [ ] Confirm: push to main → new image deployed automatically via ArgoCD, no manual steps

### Phase 6 — Monitoring
- [ ] Deploy `kube-prometheus-stack` via ArgoCD (Helm chart, not manual install)
- [ ] Add `ServiceMonitor` for FastAPI `/metrics`
- [ ] (Optional) Run `mysqld-exporter` pointed at RDS endpoint for DB metrics
- [ ] Build Grafana dashboards:
  - [ ] App: request rate, latency, error rate
  - [ ] Pods: CPU/memory usage
  - [ ] MySQL: connections, query rate (via exporter or CloudWatch)
- [ ] Set up basic alerting rules (optional but recommended for "real production")

### Phase 7 — Production Hardening (post-MVP)
- [ ] TLS on Ingress (cert-manager + Let's Encrypt, or ACM if using ALB)
- [ ] RDS Multi-AZ (failover)
- [ ] Resource requests/limits + HPA on FastAPI deployment
- [ ] Network policies (restrict pod-to-pod traffic)
- [ ] Audit/logging (CloudTrail, container logs → CloudWatch or Loki)
- [ ] Secrets rotation strategy
- [ ] Consider migrating console-created infra to Terraform

---

## 5. Security Notes (don't skip)
- UI lets users query the DB — **this is the highest-risk part of the app.** Prefer a constrained query builder (dropdowns/filters mapped to parametrized queries) over raw SQL input. If raw SQL must be supported, enforce a read-only DB user and a query allowlist/validator.
- RDS must **never** be publicly accessible.
- No AWS access keys hardcoded anywhere — use IRSA (pods) and GitHub OIDC (CI).
- ArgoCD and Grafana UIs should sit behind auth, not open LoadBalancers.

---

## 6. Open Decisions (revisit as you go)
- [ ] Ingress controller: AWS Load Balancer Controller + ALB, or NGINX ingress?
- [ ] Domain name / DNS — Route53 or external registrar?
- [ ] Multi-environment (staging + prod) or single environment for now?
- [ ] Alerting destination (Slack? email?) once Phase 6 alerting is added

---

## 7. Working Order (recap)
1. FastAPI app locally with docker-compose MySQL
2. RDS + networking in AWS console
3. EKS cluster via console, confirm pod → RDS connectivity
4. Manual deploy of app to cluster (validate end-to-end)
5. ArgoCD installed, app brought under GitOps
6. GitHub Actions CI wired to push through ArgoCD-driven deploys
7. Monitoring stack (Prometheus/Grafana)
8. Hardening pass
