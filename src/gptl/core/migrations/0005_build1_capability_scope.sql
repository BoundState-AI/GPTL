-- Slice 1 introduced governed capability/scope contracts without a persisted
-- relation. This migration preserves the owner-ratified Build 1 ordinal map so
-- later source/proposal migrations do not renumber after publication.
SELECT 1;
