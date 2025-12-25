# GAPS — DD Controller Upgrade (VFMS v0)

These are required inputs the runbook may assume but not fully specify.

## Required Operator Inputs (must collect before execution)
- Exact source model (DD9400?) and destination model (DD9900?) confirmed
- Current DDOS version on source, target DDOS version for destination
- Licensing state (features in use: DD Boost, Cloud Tier, Replication, Retention Lock)
- Network plan: IPs, masks, gateways, VLANs, DNS/NTP
- Cloud Tier details: provider, bucket/container, credentials, cloud profile signature version (s3v2/s3v4)
- Replication topology: MTrees, destinations, status, any paused links
- Client activity inventory: backups running, DDBoost connections
- Maintenance window approval + stakeholder contact list
- Physical inventory: cables, SFPs, IO cards, slot mapping, serials/service tags
- iDRAC/IPMI credentials and access method

## Stop Conditions (hard stops)
- Filesystem >95% usage (or any capacity risk)
- Active backup operations cannot be stopped
- Unresolved critical alerts on system
- Cloud Tier data-movement not stopped / not stable
- Replication unhealthy or unknown state
- Storage devices not visible after swap / cabling mismatch
