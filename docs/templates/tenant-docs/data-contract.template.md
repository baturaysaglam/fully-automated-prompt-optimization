<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Data Contract

## Dataset Inventory
- List canonical datasets and artifact roots.

## Case Schema
- Describe required fields and expected value shapes.

## Label Taxonomy
- Allowed labels and tie-break rules.

## Check Expectations
- Define scorer module and expected `score_breakdown` keys.
- `composite_score` must be 0-100 and remains the optimizer objective.
- Each `score_breakdown` value must be numeric 0-100.

## Dataset Update Procedure
- How to add/update cases and validate quality.
