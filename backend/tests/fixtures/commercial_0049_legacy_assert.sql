-- Run after upgrading the companion 0048 seed to 20261012_0049.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM platform_commercial_transfers
    WHERE id = '20000000-0000-4000-8000-000000000481'
      AND status = 'PENDING' AND received_amount = 50
      AND credit_applied = 0 AND credit_generated = 0
      AND verified_at IS NULL AND coverage_start IS NULL
  ) THEN RAISE EXCEPTION 'partial legacy payment was not preserved as pending'; END IF;
  IF EXISTS (SELECT 1 FROM platform_commercial_obligations WHERE transfer_id = '20000000-0000-4000-8000-000000000481')
  THEN RAISE EXCEPTION 'partial legacy payment gained coverage'; END IF;
  IF (SELECT coverage_through FROM platform_commercial_accounts WHERE id = '10000000-0000-4000-8000-000000000481') IS NOT NULL
  THEN RAISE EXCEPTION 'partial-only account retained stale coverage'; END IF;
  IF NOT EXISTS (
    SELECT 1 FROM platform_commercial_reconciliations
    WHERE trigger_transfer_id = '20000000-0000-4000-8000-000000000481'
      AND action = 'LEGACY_PARTIAL_REVIEW'
      AND coverage_through IS NULL
      AND pending_balance = 50
      AND detail LIKE 'Pago heredado insuficiente:%'
  ) THEN RAISE EXCEPTION 'partial legacy payment lacks an explicit review trace'; END IF;
  IF NOT EXISTS (
    SELECT 1 FROM platform_commercial_transfers
    WHERE id = '20000000-0000-4000-8000-000000000482'
      AND status = 'VERIFIED' AND credit_applied = 0 AND credit_generated = 50
  ) THEN RAISE EXCEPTION 'legacy overpayment credit is wrong'; END IF;
  IF NOT EXISTS (
    SELECT 1 FROM platform_commercial_transfers
    WHERE id = '20000000-0000-4000-8000-000000000484'
      AND status = 'VERIFIED' AND credit_applied = 50 AND credit_generated = 0
  ) THEN RAISE EXCEPTION 'legacy credit consumption is wrong'; END IF;
  IF (SELECT count(*) FROM platform_commercial_obligations WHERE account_id = '10000000-0000-4000-8000-000000000482') <> 2
  THEN RAISE EXCEPTION 'legacy verified ledger coverage is wrong'; END IF;
  IF (SELECT coverage_through FROM platform_commercial_accounts WHERE id = '10000000-0000-4000-8000-000000000482') <> '2026-10-31'
  THEN RAISE EXCEPTION 'legacy verified ledger account coverage is wrong'; END IF;
  IF EXISTS (SELECT 1 FROM platform_commercial_obligations WHERE transfer_id = '20000000-0000-4000-8000-000000000483')
  THEN RAISE EXCEPTION 'reversed legacy transfer gained coverage'; END IF;
  IF NOT EXISTS (
    SELECT 1 FROM platform_commercial_transfers
    WHERE id = '20000000-0000-4000-8000-000000000483'
      AND status = 'REVERSED' AND credit_applied = 0 AND credit_generated = 0
  ) THEN RAISE EXCEPTION 'reversed legacy transfer changed state'; END IF;
  IF (SELECT coverage_through FROM platform_commercial_accounts WHERE id = '10000000-0000-4000-8000-000000000483') IS NOT NULL
  THEN RAISE EXCEPTION 'reversed-only account retained stale coverage'; END IF;
  IF NOT EXISTS (
    SELECT 1 FROM platform_commercial_transfers
    WHERE id = '20000000-0000-4000-8000-000000000486'
      AND status = 'PENDING' AND coverage_start IS NULL AND coverage_end IS NULL
  ) THEN RAISE EXCEPTION 'mixed legacy partial payment was not returned to pending'; END IF;
  IF (SELECT count(*) FROM platform_commercial_obligations WHERE account_id = '10000000-0000-4000-8000-000000000484') <> 1
  THEN RAISE EXCEPTION 'mixed legacy account gained incorrect obligations'; END IF;
  IF (SELECT coverage_through FROM platform_commercial_accounts WHERE id = '10000000-0000-4000-8000-000000000484') <> '2026-09-30'
  THEN RAISE EXCEPTION 'mixed legacy account retained partial coverage'; END IF;
  IF NOT EXISTS (
    SELECT 1 FROM platform_commercial_reconciliations
    WHERE trigger_transfer_id = '20000000-0000-4000-8000-000000000486'
      AND action = 'LEGACY_PARTIAL_REVIEW'
      AND coverage_through = '2026-09-30'
      AND pending_balance = 60
  ) THEN RAISE EXCEPTION 'mixed legacy reconciliation snapshot is inconsistent'; END IF;
END $$;
