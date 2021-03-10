-- set showplan_all on;
-- set showplan_all off;

-- set showplan_text on;
-- set showplan_text off;

-- set statistics profile on;
-- set statistics profile off;


-- А1. Список клиентов, имеющих действующие договоры
select
	client.id_client,
	client.nameclient,
	client.inn
from (select distinct c.id_client from dbo.contract c where c.stat = 0) active_client
left join dbo.client client on client.id_client = active_client.id_client
;

select
	client.id_client,
	client.nameclient,
	client.inn
from dbo.client client
where
	client.id_client in
	(select distinct c.id_client from dbo.contract c where c.stat = 0)
;


-- А2. Список клиентов, имеющих более 3 различных типов договоров
-- Клиент в список должен попасть только один раз
select
	client.id_client,
	client.nameclient,
	client.inn,
	more_than_3.types_number
from (
select
	client_dist_types.id_client,
	count(client_dist_types.type_id) as types_number
from (select distinct
		c.id_client,
		c.type_id
	from dbo.contract c) client_dist_types
group by
	client_dist_types.id_client
having
	count(client_dist_types.type_id) > 3
) more_than_3
left join dbo.client client on client.id_client = more_than_3.id_client
;


-- А3. Получить отчет со списком количества клиентов в разрезе типов договоров
-- Учитывать только действующие договоры
select
	contract.type_id,
	count(client.id_client) as cnt
from dbo.contract contract
left join dbo.client client on client.id_client = contract.id_client and contract.stat = 0
group by
	contract.type_id
;

select
	contract.type_id,
	count(client.id_client) as cnt
from dbo.contract contract
left join dbo.client client on client.id_client = contract.id_client
where
	contract.stat = 0
group by
	contract.type_id
;


-- А4. Получить отчет со списком количества договоров с незаполненным (NULL) комментарием
select
	c.type_id,
	c.stat,
	count(1) as cnt
from dbo.contract c
where
	c.descr is null
group by
	c.type_id,
	c.stat
;


-- Б5. Вывести эффективную ставку по каждому договору
-- Формула расчета = (Сумма всех комиссий/Сумма договора) * 100%
select
	client.nameclient,
	contract.[number],
	contract.stat,
	contract.value_contract,
	sum(coalesce(commission.value_commission, 0)) / contract.value_contract * 100 as tax_calc
from dbo.contract contract
left join dbo.commission commission on contract.id_contract = commission.id_contract
left join dbo.client client on client.id_client = contract.id_client
-- по условию не совсем ясно, требуется ли учитывать все комиссии
-- или только те, которые действуют в текущий момент;
-- в последнем случае условие ниже нужно раскомментировать
--where
--	getdate() between commission.date_begin and commission.date_end
group by
	client.nameclient,
	contract.[number],
	contract.stat,
	contract.value_contract
;


-- В6. Необходимо написать SQL код, проверяющий корректность ИНН клиента по контрольному ключу.
if object_id (N'dbo.is_inn_correct', N'FN') is not null
	drop function dbo.is_inn_correct;

create function dbo.is_inn_correct(@inn varchar(12)) 
returns bit as 
begin 
	declare @c table(pos int, m10 int, m11 int, m12 int)
	insert @c
		  select 1,  2,  7,  3
	union select 2,	 4,  2,  7
	union select 3,  10, 4,  2
	union select 4,  3,  10, 4
	union select 5,  5,  3,  10
	union select 6,  9,  5,  3
	union select 7,  4,  9,  5
	union select 8,  6,  4,  9
	union select 9,  8,  6,  4
	union select 10, 0,  8,  6
	union select 11, 0,  0,  8

	declare @s10  int, @s11 int, @s12 int

	select 
	 	@s10 = sum(convert(int,substring(@inn + '00', pos, 1)) * m10),
	  	@s11 = sum(convert(int,substring(@inn + '00', pos, 1)) * m11),
	  	@s12 = sum(convert(int,substring(@inn + '00', pos, 1)) * m12)
	from @c

	declare @correct varchar(12)

	select
		@s10 = (@s10 % 11) % 10,
		@s11 = (@s11 % 11) % 10,
		@s12 = (@s12 % 11) % 10
	
	select @correct=
	  	case datalength(@inn) 
	    	when 10 then left(@inn, 9) + convert(char, @s10)
	    	when 12 then left(@inn, 10) + convert(varchar, @s11) + convert(varchar, @s12)
	    	else '!' + @inn
	  	end
	
	if @correct = @inn
		return 1
	return 0
end;

select dbo.is_inn_correct('4235355520');
select dbo.is_inn_correct('4235355521');
