-- name: insert_roll!
insert into rolls 
values (:member_id, :member_nick, :member_name, :roll, :tag, :result, :time);

-- name: get_rolls
select * from rolls
order by time desc
limit :max_rolls;

-- name: get_user_rolls
select * from rolls
where member_id=:member_id
order by time desc
limit :max_rolls;

-- name: get_last_user_roll^
select * from rolls
where member_id=:member_id
order by time desc
limit 1;

-- name: set_user_var!
insert into user_vars
values (:member_id, :var, :val)
on conflict (member_id, var)
do update set val=:val;

-- name: get_user_var^
select * from user_vars
where member_id=:member_id and var=:var;

-- name: get_user_vars
select * from user_vars
where member_id=:member_id;

-- name: del_user_var!
delete from user_vars
where member_id=:member_id and var=:var;

-- name: set_guild_var!
insert into guild_vars
values (:member_id, :var, :val)
on conflict (var)
do update set member_id=:member_id, val=:val;

-- name: get_guild_var^
select * from guild_vars
where var=:var;

-- name: del_guild_var!
delete from guild_vars
where var=:var;

-- name: get_guild_vars
select * from guild_vars;
