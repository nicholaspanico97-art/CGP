"""
Named people (v1.33, ROADMAP item 7).

The model keeps `lab.stars` as a float and moves it through the talent
market. This is a roster laid over it: each whole star is a named
researcher, and when a lab's count rises or falls the roster changes
with names - a join from the pool, a departure, and when one lab loses
in the month another gains, a poach. Nothing here changes an outcome;
it draws no randomness (names come from a fixed list, in order).
"""
FIRST = ["Ada", "Wen", "Priya", "Tomasz", "Yuki", "Amara", "Dmitri", "Sofia", "Kwame",
         "Leila", "Marcus", "Ines", "Ravi", "Hana", "Jonas", "Mei", "Elias", "Noor",
         "Felix", "Aiko", "Omar", "Greta", "Sven", "Zara", "Ibrahim", "Clara", "Kenji",
         "Rosa", "Anders", "Lucia", "Tariq", "Ingrid", "Mateo", "Sana", "Otto", "Ayla"]
LAST = ["Okafor", "Lindqvist", "Nakamura", "Haddad", "Petrov", "Brennan", "Osei",
        "Fischer", "Iyer", "Moreau", "Zhou", "Almeida", "Kovacs", "Rahman", "Silva",
        "Tanaka", "Novak", "Dubois", "Mensah", "Larsen", "Bhatt", "Costa", "Weber",
        "Sato", "Ferreira", "Ahmed", "Nilsen", "Rossi", "Kim", "Varga"]


class Roster:
    def __init__(self):
        self.next_id = 0
        self.people = {}            # name -> lab name (or None, in the pool)
        self.by_lab = {}            # lab name -> [names]
        self.events = []            # (month, text)
        self.pending_loss = {}      # lab -> names that left this month (for poach matching)

    def _new_name(self):
        i = self.next_id
        self.next_id += 1
        return f"{FIRST[i % len(FIRST)]} {LAST[(i // len(FIRST) + i) % len(LAST)]}"

    def sync(self, world):
        """Bring the roster to this month's star counts, naming the moves."""
        m = world.month
        losses, gains = {}, {}
        for lab in world.labs:
            names = self.by_lab.setdefault(lab.name, [])
            want = int(round(lab.stars))
            if want < len(names):
                gone = names[want:]
                del names[want:]
                losses[lab.name] = gone
            elif want > len(names):
                gains[lab.name] = want - len(names)
        # match departures to arrivals as poaches; the rest join from the pool
        free = [(src, n) for src, ns in losses.items() for n in ns]
        for lab_name, k in gains.items():
            for _ in range(k):
                if free:
                    src, n = free.pop(0)
                    self.by_lab[lab_name].append(n)
                    self.people[n] = lab_name
                    self.events.append((m, f"{n} left {src} for {lab_name}"))
                else:
                    n = self._new_name()
                    self.by_lab[lab_name].append(n)
                    self.people[n] = lab_name
                    if m > 0:
                        self.events.append((m, f"{n} joined {lab_name}"))
        for src, n in free:
            self.people[n] = None
            self.events.append((m, f"{n} left {src}"))
        # a dead lab's people are already accounted through its stars moving

    def of(self, lab_name):
        return list(self.by_lab.get(lab_name, []))
