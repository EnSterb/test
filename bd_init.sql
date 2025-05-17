
drop table if exists users;
CREATE TABLE if not exists users(
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

drop table if exists links;
create table if not exists links(
    id int generated always as IDENTITY PRIMARY KEY,
    user_id int not null,
    title text not null,
    description text,
    url TEXT NOT NULL UNIQUE,
    image text,
    type TEXT DEFAULT 'website' CHECK (type IN ('website', 'book', 'article', 'music', 'video')),
    created_at TIMESTAMP default current_timestamp,
    updated_at timestamp default current_timestamp,

    constraint fk_user foreign key (user_id) references users (id) on delete cascade
);

drop table if exists collections;
CREATE TABLE IF NOT EXISTS collections (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP default current_timestamp,
    updated_at timestamp default current_timestamp,

    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

DROP TABLE IF EXISTS collection_links;
CREATE TABLE IF NOT EXISTS collection_links (
    collection_id INT NOT NULL,
    link_id INT NOT NULL,
    PRIMARY KEY (collection_id, link_id),

    CONSTRAINT fk_collection FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE,
    CONSTRAINT fk_link FOREIGN KEY (link_id) REFERENCES links(id) ON DELETE CASCADE
);

TRUNCATE TABLE users, links, collections, collection_links RESTART IDENTITY CASCADE;

-- Вставляем 20 пользователей
DO $$
BEGIN
  FOR i IN 1..20 LOOP
    INSERT INTO users (email, password_hash)
    VALUES (
      format('user%s@example.com', i),
      format('hash%s', i)
    );
  END LOOP;
END $$;


-- Добавляем ссылки, коллекции и связи
DO $$
DECLARE
  u_id INT;
  link_id INT;
  collection1_id INT;
  collection2_id INT;
  type TEXT;
  types TEXT[] := ARRAY['website', 'book', 'article', 'music', 'video'];
  base_url TEXT := 'https://example.com';
BEGIN
  FOR u_id IN 1..20 LOOP
    -- Создаём первую коллекцию
    INSERT INTO collections (user_id, name, description)
    VALUES (
      u_id,
      format('Collection A of user %s', u_id),
      'Auto-generated collection A'
    )
    RETURNING id INTO collection1_id;

    -- Создаём вторую коллекцию
    INSERT INTO collections (user_id, name, description)
    VALUES (
      u_id,
      format('Collection B of user %s', u_id),
      'Auto-generated collection B'
    )
    RETURNING id INTO collection2_id;

    -- Создаём по одной ссылке каждого типа
    FOREACH type IN ARRAY types LOOP
      INSERT INTO links (user_id, title, description, url, image, "type")
      VALUES (
        u_id,
        format('%s link for user %s', INITCAP(type), u_id),
        format('A test %s description for user %s', type, u_id),
        format('%s/%s/user%s', base_url, type, u_id),
        format('%s/img/%s_user%s.png', base_url, type, u_id),
        type
      )
      RETURNING id INTO link_id;

      -- Добавим ссылку в обе коллекции
      INSERT INTO collection_links (collection_id, link_id) VALUES (collection1_id, link_id);
      INSERT INTO collection_links (collection_id, link_id) VALUES (collection2_id, link_id);
    END LOOP;
  END LOOP;
END $$;

DROP TABLE IF EXISTS password_tokens;
CREATE TABLE IF NOT EXISTS password_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);