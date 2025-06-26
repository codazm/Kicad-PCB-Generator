# Database Schema Design

## Overview
The database schema is designed to support the storage and retrieval of PCB components, designs, and related metadata. It uses a flexible schema that can be extended as needed while maintaining data integrity and performance.

## Core Principles
1. **Flexibility**: Schema should accommodate different component types and properties
2. **Performance**: Optimized for common query patterns
3. **Integrity**: Strong data validation and constraints
4. **Extensibility**: Easy to add new tables and relationships
5. **Versioning**: Support for schema evolution

## Schema Design

### Core Tables

#### Components
```sql
CREATE TABLE components (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    CONSTRAINT unique_component_name UNIQUE (name)
);

CREATE INDEX idx_components_type ON components(type);
CREATE INDEX idx_components_metadata ON components USING GIN (metadata);
```

#### Component Properties
```sql
CREATE TABLE component_properties (
    id UUID PRIMARY KEY,
    component_id UUID REFERENCES components(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_component_property UNIQUE (component_id, key)
);

CREATE INDEX idx_component_properties_component_id ON component_properties(component_id);
CREATE INDEX idx_component_properties_key ON component_properties(key);
```

#### Designs
```sql
CREATE TABLE designs (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    CONSTRAINT unique_design_name UNIQUE (name)
);

CREATE INDEX idx_designs_metadata ON designs USING GIN (metadata);
```

#### Design Components
```sql
CREATE TABLE design_components (
    id UUID PRIMARY KEY,
    design_id UUID REFERENCES designs(id) ON DELETE CASCADE,
    component_id UUID REFERENCES components(id) ON DELETE CASCADE,
    position_x DECIMAL(10,2),
    position_y DECIMAL(10,2),
    rotation DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    CONSTRAINT unique_design_component UNIQUE (design_id, component_id)
);

CREATE INDEX idx_design_components_design_id ON design_components(design_id);
CREATE INDEX idx_design_components_component_id ON design_components(component_id);
```

#### Connections
```sql
CREATE TABLE connections (
    id UUID PRIMARY KEY,
    design_id UUID REFERENCES designs(id) ON DELETE CASCADE,
    from_component_id UUID REFERENCES design_components(id) ON DELETE CASCADE,
    to_component_id UUID REFERENCES design_components(id) ON DELETE CASCADE,
    connection_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    CONSTRAINT unique_connection UNIQUE (design_id, from_component_id, to_component_id)
);

CREATE INDEX idx_connections_design_id ON connections(design_id);
CREATE INDEX idx_connections_from_component ON connections(from_component_id);
CREATE INDEX idx_connections_to_component ON connections(to_component_id);
```

### Audit Tables

#### Component History
```sql
CREATE TABLE component_history (
    id UUID PRIMARY KEY,
    component_id UUID REFERENCES components(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    changes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id UUID
);

CREATE INDEX idx_component_history_component_id ON component_history(component_id);
CREATE INDEX idx_component_history_action ON component_history(action);
```

#### Design History
```sql
CREATE TABLE design_history (
    id UUID PRIMARY KEY,
    design_id UUID REFERENCES designs(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    changes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id UUID
);

CREATE INDEX idx_design_history_design_id ON design_history(design_id);
CREATE INDEX idx_design_history_action ON design_history(action);
```

## Design Assumptions
1. Components will have unique identifiers
2. Components will have properties stored as JSONB
3. Designs will reference multiple components
4. Components can be connected in designs
5. History tracking is required
6. Metadata will be stored as JSONB
7. Timestamps will be timezone-aware
8. UUIDs will be used for primary keys

## Next Steps
1. Create database migration scripts
2. Implement data access layer
3. Add data validation
4. Add data migration tools
5. Add backup and restore functionality
6. Add performance monitoring
7. Add data integrity checks
8. Add schema versioning

## Notes
- This design is subject to change based on Phase 1 requirements
- Focus on creating flexible schemas that can be extended
- Document any assumptions that might need to be revised
- Regular synchronization with Phase 1 work is essential
- Consider performance implications of JSONB fields
- Plan for future schema evolution 