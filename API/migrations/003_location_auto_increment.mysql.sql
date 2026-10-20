-- Si location a été créée par import SQL sans auto-incrément.
ALTER TABLE location MODIFY COLUMN id INTEGER NOT NULL AUTO_INCREMENT;
