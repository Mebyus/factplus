import datetime
import random

target_batch_size = 100
target_script_size = 50_000

number_of_types = 24
type_affinities = [6, 2, 3, 1, 4, 1, 8, 0.5, 1, 2, 2, 0.3]

number_of_clients = 200_000
person_weight = 0.8
company_weight = 0.2
first_names_dictionary_path = "first-names.txt"
last_names_dictionary_path = "last-names.txt"

max_contracts_per_client = 9
contract_min_value = 15000.0
contract_max_value = 80000.0
active_contract_probability = 0.85
contract_has_description_probability = 0.7

max_commissions_per_contract = 5
commission_min_start_date = datetime.date.fromisoformat(
    "2018-04-26").toordinal()
commission_max_end_date = datetime.date.fromisoformat("2023-12-05").toordinal()
commission_max_stake = 0.1


class TypePool:
    def __init__(self, number: int, affinities: list[float]):
        self.number = number
        temp_affinities = [a for a in affinities]
        if len(temp_affinities) < number:
            temp_affinities += [1 for i in range(len(temp_affinities), number)]
        total = sum(temp_affinities)
        for i in range(len(temp_affinities)):
            temp_affinities[i] = temp_affinities[i] / total
        self.affinities = temp_affinities
        self.thresholds = []
        s = 0
        for a in self.affinities:
            s += a
            self.thresholds.append(s)

    def index(self) -> int:
        r = random.random()
        for i in range(len(self.thresholds)):
            if r < self.thresholds[i]:
                return i+1
        return 0

    def generate(self):
        return [self.index()]


class ContractPool:
    def __init__(self, min_value: float, max_value: float, active_prob: float, desc_prob: float):
        self.min_value = min_value
        self.max_value = max_value
        self.active_prob = active_prob
        self.desc_prob = desc_prob
        self.first_letter = ["D", "A", "T", "N", "C"]
        self.middle_letter = ["K", "T", "P", "M", "C"]
        self.last_letter = ["f", "s", "a", "x", "z", "k", "u", "e"]
        self.id = 0

    def value(self) -> float:
        return random.random() * (self.max_value - self.min_value) + self.min_value

    def description(self):
        if random.random() < self.desc_prob:
            return "Description"
        else:
            return None

    def active(self) -> int:
        if random.random() < self.active_prob:
            return 0
        else:
            return 1

    def number(self) -> str:
        return random.choice(self.first_letter) + str(random.randint(1000, 9999)) + "-" \
            + random.choice(self.middle_letter) + str(random.randint(10000, 99999)) \
            + random.choice(self.last_letter) + "-" + \
            str(random.randint(10, 99))

    def generate(self, client_id: int, type_id: int):
        self.id += 1
        return [self.id, client_id, type_id, self.active(), self.value(), self.number(), self.description()]


class CommissionPool:
    def __init__(self, min_date: int, max_date: int, max_fraction_value: float):
        self.min_date = min_date
        self.max_date = max_date
        self.max_fraction_value = max_fraction_value
        self.id = 0

    def date_range(self) -> tuple([int, int]):
        start_date = random.randint(self.min_date, self.max_date)
        end_date = random.randint(start_date, self.max_date)
        return start_date, end_date

    def value(self, contract_value: float) -> float:
        return self.max_fraction_value * random.random() * contract_value

    def generate(self, contract_id: int, contract_value: float):
        self.id += 1
        date_range = self.date_range()
        date_start = datetime.date.fromordinal(date_range[0]).isoformat()
        date_end = datetime.date.fromordinal(date_range[1]).isoformat()
        return [self.id, contract_id, date_start, date_end, self.value(contract_value)]


class FullNamePool:
    def __init__(self, first_names: list[str], last_names: list[str]):
        self.first_names = list(first_names)
        self.last_names = list(last_names)

    def generate(self) -> str:
        return self.last() + " " + self.first()

    def first(self) -> str:
        return random.choice(self.first_names).strip().replace("'", "''")

    def last(self) -> str:
        return random.choice(self.last_names).strip().replace("'", "''")


class INNPool:
    def __init__(self, person_weight: float, company_weight: float):
        if person_weight < 0 or company_weight < 0:
            raise Exception("Negative weight argument")
        total = person_weight + company_weight
        self.pp = person_weight / total
        self.cp = company_weight / total

    def generate(self) -> str:
        if random.random() < self.pp:
            return str(self.person())
        else:
            return str(self.company())

    def person(self) -> int:
        return random.randint(100_000_000_000, 1_000_000_000_000 - 1)

    def company(self) -> int:
        return random.randint(1_000_000_000, 10_000_000_000 - 1)


class ClientPool:
    def __init__(self, name_pool: FullNamePool, inn_pool: INNPool):
        self.name_pool = name_pool
        self.inn_pool = inn_pool
        self.id = 0

    def generate(self):
        self.id += 1
        return [self.id, self.inn_pool.generate(), self.name_pool.generate()]


class DataPool:
    def __init__(self, client_pool: ClientPool, type_pool: TypePool,
                 contract_pool: ContractPool, commission_pool: CommissionPool,
                 max_contracts_per_client: int, max_commissions_per_contract: int):
        self.client_pool = client_pool
        self.type_pool = type_pool
        self.contract_pool = contract_pool
        self.commission_pool = commission_pool
        self.max_contracts_per_client = max_contracts_per_client
        self.max_commissions_per_contract = max_commissions_per_contract
        self.clients = []
        self.contracts = []
        self.commissions = []

    def next_client(self):
        client_row = self.client_pool.generate()
        self.clients.append(client_row)
        client_id = client_row[0]
        self.make_contracts(client_id)

    def make_contracts(self, client_id: int):
        contracts = random.randint(0, self.max_contracts_per_client)
        for _ in range(contracts):
            contract_row = self.contract_pool.generate(
                client_id, self.type_pool.generate()[0])
            self.contracts.append(contract_row)
            self.make_commissions(contract_row[0], contract_row[4])

    def make_commissions(self, contract_id: int, contract_value: float):
        commissions = random.randint(0, self.max_commissions_per_contract)
        for _ in range(commissions):
            commission_row = self.commission_pool.generate(
                contract_id, contract_value)
            self.commissions.append(commission_row)

    def more_clients_than(self, threshold: int) -> bool:
        return len(self.clients) > threshold

    def more_contracts_than(self, threshold: int) -> bool:
        return len(self.contracts) > threshold

    def more_commissions_than(self, threshold: int) -> bool:
        return len(self.commissions) > threshold

    def flush_clients(self):
        c = self.clients
        self.clients = []
        return c

    def flush_contracts(self):
        c = self.contracts
        self.contracts = []
        return c

    def flush_commissions(self):
        c = self.commissions
        self.commissions = []
        return c


class ScriptCollector:
    def __init__(self, max_rows: int, table: str, columns: list[str], prefix: str, suffix: str):
        self.table = table
        self.columns = columns
        self.prefix = prefix
        self.suffix = suffix
        self.max_rows = max_rows
        self.current_rows = 0
        self.counter = 0
        self.f = None
        self.open_next()

    def write(self, rows):
        write_insert_statement(self.f, self.table, self.columns, rows)
        self.current_rows += len(rows)
        if self.current_rows > self.max_rows:
            self.open_next()
            self.current_rows = 0

    def next_name(self) -> str:
        self.counter += 1
        return "{0}_{1:0>3d}_{2}.sql".format(self.prefix, self.counter, self.suffix)

    def open_next(self):
        self.close()
        self.f = open(self.next_name(), "w")
        write_set_session_settings(self.f, self.table)

    def close(self):
        if self.f:
            self.f.close()


def lines_from_file(path: str) -> list[str]:
    with open(path, "r") as f:
        return f.readlines()


def stringify_value(value) -> str:
    if value is None:
        return "null"
    if type(value) is str:
        return "\'" + value + "\'"
    return str(value)


def stringify_row(row_values) -> str:
    return "(" + ", ".join([stringify_value(x) for x in row_values]) + ")"


def write_insert_statement(f, table: str, columns: list[str], values):
    f.write("insert into {0}({1}) values\n{2};\n".format(
        table, ", ".join(columns), ",\n".join([stringify_row(row) for row in values])))


def write_set_session_settings(f, table: str):
    f.write("set identity_insert {0} on;\n".format(table))
    f.write("set quoted_identifier on;\n")


def create_contract_type_sql(number_of_types: int):
    with open("01_contract_types.sql", "w") as f:
        write_set_session_settings(f, "dbo.contract_type")
        write_insert_statement(f, "dbo.contract_type", ["type_id"], [
            [i] for i in range(1, number_of_types+1)])


def main():
    random.seed()
    create_contract_type_sql(number_of_types)
    inn_pool = INNPool(person_weight, company_weight)
    name_pool = FullNamePool(lines_from_file(
        first_names_dictionary_path), lines_from_file(last_names_dictionary_path))
    commission_pool = CommissionPool(commission_min_start_date, commission_max_end_date,
                                     commission_max_stake)
    contract_pool = ContractPool(contract_min_value, contract_max_value,
                                 active_contract_probability, contract_has_description_probability)
    client_pool = ClientPool(name_pool, inn_pool)
    type_pool = TypePool(number_of_types, type_affinities)
    data_pool = DataPool(client_pool, type_pool, contract_pool, commission_pool,
                         max_contracts_per_client, max_commissions_per_contract)

    client_columns = ["id_client", "inn", "nameclient"]
    contract_columns = ["id_contract", "id_client", "type_id",
                        "stat", "value_contract", "\"number\"", "descr"]
    commission_columns = ["id_commission", "id_contract",
                          "date_begin", "date_end", "value_commission"]

    client_collector = ScriptCollector(
        target_script_size, "dbo.client", client_columns, "01", "clients")
    contract_collector = ScriptCollector(
        target_script_size, "dbo.contract", contract_columns, "02", "contracts")
    commissions_collector = ScriptCollector(
        target_script_size, "dbo.commission", commission_columns, "03", "commissions")

    progress = 0.0
    for i in range(number_of_clients):
        percent = 100 * i / number_of_clients
        if percent > progress:
            progress += 5.0
            print("{0}%".format(round(percent)))
        data_pool.next_client()
        if data_pool.more_clients_than(target_batch_size):
            client_collector.write(data_pool.flush_clients())
        if data_pool.more_contracts_than(target_batch_size):
            contract_collector.write(data_pool.flush_contracts())
        if data_pool.more_commissions_than(target_batch_size):
            commissions_collector.write(data_pool.flush_commissions())

    if data_pool.more_clients_than(0):
        client_collector.write(data_pool.flush_clients())
    if data_pool.more_contracts_than(0):
        contract_collector.write(data_pool.flush_contracts())
    if data_pool.more_commissions_than(0):
        commissions_collector.write(data_pool.flush_commissions())

    client_collector.close()
    contract_collector.close()
    commissions_collector.close()


if __name__ == "__main__":
    main()
