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
  IF EXISTS (SELECT 1 FROM platform_commercial_obligations WHERE transfer_id = '20000000-0000-4000-8000-000000000483')
  THEN RAISE EXCEPTION 'reversed legacy transfer gained coverage'; END IF;
  IF NOT EXISTS (
    SELECT 1 FROM platform_commercial_transfers
    WHERE id = '20000000-0000-4000-8000-000000000483'
      AND status = 'REVERSED' AND credit_applied = 0 AND credit_generated = 0
  ) THEN RAISE EXCEPTION 'reversed legacy transfer changed state'; END IF;
END $$;
