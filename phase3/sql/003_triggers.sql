-- ============================================================================
-- 003_triggers.sql — integrity triggers (optional but demonstrates DBMS features).
-- ============================================================================

DROP TRIGGER IF EXISTS trg_customers_loyalty_on_paid;
DELIMITER $$

-- Award 1 loyalty point per currency unit spent when an order transitions to 'paid'.
CREATE TRIGGER trg_customers_loyalty_on_paid
AFTER UPDATE ON orders
FOR EACH ROW
BEGIN
    IF NEW.status = 'paid' AND OLD.status <> 'paid' THEN
        UPDATE customers
           SET loyalty_points = loyalty_points + FLOOR(NEW.grand_total)
         WHERE user_id = NEW.customer_user_id;
    END IF;
END$$

DELIMITER ;


DROP TRIGGER IF EXISTS trg_inventory_reserve_on_order;
DELIMITER $$

-- Reserve stock when an order item is inserted (decreases qty_available
-- indirectly via qty_reserved). Only the first warehouse with qty_on_hand
-- is selected; production code would handle multi-warehouse allocation.
CREATE TRIGGER trg_inventory_reserve_on_order
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    UPDATE inventory
       SET qty_reserved = qty_reserved + NEW.quantity
     WHERE product_id = NEW.product_id
       AND variant_no = NEW.variant_no
       AND qty_on_hand - qty_reserved >= NEW.quantity
     LIMIT 1;
END$$

DELIMITER ;


DROP TRIGGER IF EXISTS trg_discount_usage_bump;
DELIMITER $$

-- Increment discount.used_count when a usage row is inserted.
CREATE TRIGGER trg_discount_usage_bump
AFTER INSERT ON discount_usages
FOR EACH ROW
BEGIN
    UPDATE discounts
       SET used_count = used_count + 1
     WHERE discount_id = NEW.discount_id;
END$$

DELIMITER ;

-- End of 003_triggers.sql
