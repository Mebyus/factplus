create table dbo.client(
	id_client int not null identity primary key,
	inn varchar(16),
	nameclient varchar(30)
);

create table dbo.contract_type(
	type_id int not null identity primary key,
	name varchar(30),
	descr varchar(255)
);

create table dbo.contract(
	id_contract int not null identity primary key,
	id_client int not null,
	type_id int not null,
	stat int not null default 0,
	value_contract decimal(18,6),
	"number" varchar(30),
	descr varchar(255),
	
	constraint fk_client foreign key (id_client) references dbo.client(id_client),
	constraint fk_contract_type foreign key (type_id) references dbo.contract_type(type_id),
	
	index i_contract_id_client (id_client)
);

create table dbo.commission(
	id_commission int not null identity primary key,
	id_contract int not null,
	date_begin date,
	date_end date,
	value_commission decimal(18,6),
	
	constraint fk_contract foreign key (id_contract) references dbo.contract(id_contract),
	
	index i_commission_id_contract (id_contract)
);
