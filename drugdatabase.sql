-- drugdatabase.sql — SQLite schema for the Pharmacy Management System
--
-- NOTE: Tables are created programmatically by database.py (create_all_tables).
-- This file serves as the authoritative schema reference.
--
-- Previous version used MySQL syntax (CREATE SCHEMA, USE, AUTO_INCREMENT,
-- DELIMITER //) which is invalid in SQLite.  This file is now valid SQLite.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Customers
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Customers (
    C_Name     VARCHAR(50)  NOT NULL,
    C_Password VARCHAR(200) NOT NULL,    -- PBKDF2-SHA256: <salt_hex>:<dk_hex>
    C_Email    VARCHAR(50)  PRIMARY KEY NOT NULL,
    C_State    VARCHAR(50)  NOT NULL,
    C_Number   VARCHAR(50)  NOT NULL
);

-- ---------------------------------------------------------------------------
-- Drugs
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Drugs (
    D_Name    VARCHAR(50)  NOT NULL,
    D_ExpDate DATE         NOT NULL,
    D_Use     VARCHAR(200) NOT NULL,
    D_Qty     INT          NOT NULL CHECK(D_Qty >= 0),  -- prevents negative stock
    D_id      VARCHAR(50)  PRIMARY KEY NOT NULL,
    D_Price   REAL         NOT NULL DEFAULT 0.0,
    D_Image   TEXT         DEFAULT NULL                 -- filename in images/ dir
);

-- ---------------------------------------------------------------------------
-- Orders  (header row per order)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Orders (
    O_id        VARCHAR(100) PRIMARY KEY NOT NULL,  -- UUID-based, e.g. alice#A1B2C3D4
    O_Name      VARCHAR(100) NOT NULL,              -- customer name
    O_Timestamp TEXT         NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------------
-- OrderItems  (one row per drug per order — replaces comma-string O_Items/O_Qty)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS OrderItems (
    OI_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    O_id       VARCHAR(100) NOT NULL,
    D_id       VARCHAR(50)  NOT NULL,
    D_name     VARCHAR(50)  NOT NULL,               -- denormalised for history
    quantity   INT          NOT NULL CHECK(quantity > 0),
    unit_price REAL         NOT NULL DEFAULT 0.0,   -- price at time of order
    FOREIGN KEY (O_id) REFERENCES Orders(O_id) ON DELETE CASCADE,
    FOREIGN KEY (D_id) REFERENCES Drugs(D_id)
);

-- ---------------------------------------------------------------------------
-- Useful views (optional — not used by the app, handy for manual queries)
-- ---------------------------------------------------------------------------

-- Full order detail
CREATE VIEW IF NOT EXISTS v_order_detail AS
SELECT
    o.O_id,
    o.O_Name      AS customer,
    o.O_Timestamp AS ordered_at,
    oi.D_id,
    oi.D_name,
    oi.quantity,
    oi.unit_price,
    (oi.quantity * oi.unit_price) AS line_total
FROM Orders o
JOIN OrderItems oi ON o.O_id = oi.O_id;

-- Order totals per customer
CREATE VIEW IF NOT EXISTS v_customer_totals AS
SELECT
    O_Name                       AS customer,
    COUNT(DISTINCT O_id)         AS order_count,
    SUM(quantity * unit_price)   AS total_spent
FROM v_order_detail
GROUP BY O_Name;

-- Low-stock drugs (at or below 10 units)
CREATE VIEW IF NOT EXISTS v_low_stock AS
SELECT D_Name, D_id, D_Qty
FROM Drugs
WHERE D_Qty <= 10;
