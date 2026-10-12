-- Run only on a disposable local database stamped at 20261012_0048.
INSERT INTO empresas (id, nombre, slug, estado, is_active) VALUES
  ('00000000-0000-4000-8000-000000000481', 'Legacy Partial', 'legacy-partial', 'Activa', true),
  ('00000000-0000-4000-8000-000000000482', 'Legacy Ledger', 'legacy-ledger', 'Activa', true),
  ('00000000-0000-4000-8000-000000000483', 'Legacy Reversed', 'legacy-reversed', 'Activa', true),
  ('00000000-0000-4000-8000-000000000484', 'Legacy Mixed', 'legacy-mixed', 'Activa', true);

INSERT INTO platform_commercial_accounts
  (id, company_id, plan_type, monthly_fee, currency, service_start_date, coverage_through, credit_balance, is_active)
VALUES
  ('10000000-0000-4000-8000-000000000481', '00000000-0000-4000-8000-000000000481', 'STANDARD', 100, 'USD', '2026-09-01', '2026-09-30', 0, true),
  ('10000000-0000-4000-8000-000000000482', '00000000-0000-4000-8000-000000000482', 'STANDARD', 100, 'USD', '2026-09-01', '2026-10-31', 0, true),
  ('10000000-0000-4000-8000-000000000483', '00000000-0000-4000-8000-000000000483', 'STANDARD', 100, 'USD', '2026-09-01', '2026-09-30', 0, true),
  ('10000000-0000-4000-8000-000000000484', '00000000-0000-4000-8000-000000000484', 'STANDARD', 100, 'USD', '2026-09-01', '2026-10-31', 0, true);

INSERT INTO platform_commercial_transfers
  (id, company_id, account_id, transfer_date, received_amount, agreed_amount, months_covered, reference, status, idempotency_key, coverage_start, coverage_end, verified_at, reversed_at, reversal_reason, is_active)
VALUES
  ('20000000-0000-4000-8000-000000000481', '00000000-0000-4000-8000-000000000481', '10000000-0000-4000-8000-000000000481', '2026-09-05', 50, 100, 1, 'PARTIAL', 'VERIFIED', 'legacy-partial-key', '2026-09-01', '2026-09-30', '2026-09-05 10:00:00+00', NULL, NULL, true),
  ('20000000-0000-4000-8000-000000000482', '00000000-0000-4000-8000-000000000482', '10000000-0000-4000-8000-000000000482', '2026-09-05', 150, 100, 1, 'OVERPAY', 'VERIFIED', 'legacy-overpay-key', '2026-09-01', '2026-09-30', '2026-09-05 10:00:00+00', NULL, NULL, true),
  ('20000000-0000-4000-8000-000000000484', '00000000-0000-4000-8000-000000000482', '10000000-0000-4000-8000-000000000482', '2026-10-05', 50, 100, 1, 'USES-CREDIT', 'VERIFIED', 'legacy-credit-use-key', '2026-10-01', '2026-10-31', '2026-10-05 10:00:00+00', NULL, NULL, true),
  ('20000000-0000-4000-8000-000000000483', '00000000-0000-4000-8000-000000000483', '10000000-0000-4000-8000-000000000483', '2026-09-05', 300, 100, 1, 'REVERSED', 'REVERSED', 'legacy-reversed-key', '2026-09-01', '2026-09-30', '2026-09-05 10:00:00+00', '2026-09-06 10:00:00+00', 'Transferencia devuelta', true),
  ('20000000-0000-4000-8000-000000000485', '00000000-0000-4000-8000-000000000484', '10000000-0000-4000-8000-000000000484', '2026-09-05', 100, 100, 1, 'MIXED-PAID', 'VERIFIED', 'legacy-mixed-paid-key', '2026-09-01', '2026-09-30', '2026-09-05 10:00:00+00', NULL, NULL, true),
  ('20000000-0000-4000-8000-000000000486', '00000000-0000-4000-8000-000000000484', '10000000-0000-4000-8000-000000000484', '2026-10-05', 40, 100, 1, 'MIXED-PARTIAL', 'VERIFIED', 'legacy-mixed-partial-key', '2026-10-01', '2026-10-31', '2026-10-05 10:00:00+00', NULL, NULL, true);
