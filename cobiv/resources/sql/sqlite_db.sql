create table catalog (id INTEGER PRIMARY KEY, name text);
create table repository (id INTEGER PRIMARY KEY, catalog_key int, path text, recursive num);
create table file (id INTEGER PRIMARY KEY, repo_key int, name text, searchable int, file_type text);
create table core_tags (file_key int, path text, size int, file_date datetime, ext text);
create table tag (file_key int, category int, kind text, type int, value);
create table set_head (id INTEGER PRIMARY KEY, name text, readonly num);
create table set_detail (set_head_key int, position int, file_key int);
create table file_map (parent_key int, child_key int, position int);
create unique index file_map_idx on file_map(parent_key,child_key);
create unique index file_idx1 on file(name);
create index tag_idx1 on tag(file_key);
create index tag_idx2 on tag(kind,value);
create index tag_idx3 on tag(value);
create unique index core_tags_idx1 on core_tags(file_key);
create index core_tags_idx2 on core_tags(path,size,file_date,ext);
create unique index set_detail_pos_idx on set_detail(set_head_key,position);
create unique index set_detail_file_idx on set_detail(set_head_key,file_key);