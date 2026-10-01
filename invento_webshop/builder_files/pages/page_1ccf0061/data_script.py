topic = frappe.form_dict.get("topic")
search = frappe.form_dict.get("search")

filters = []
or_filters = []

if topic:
    filters.append(["FAQ", "topic", "=", topic])

if search:
    or_filters = [
        ["FAQ", "question", "like", f"%{search}%"],
        ["FAQ", "answer", "like", f"%{search}%"]
    ]

faqs = frappe.get_all(
    "FAQ",
    filters=filters,
    or_filters=or_filters,
    fields=["topic", "question", "answer"]
)

faq_filters = [
  {
    "name": "Finishes Lacquer",
    "url": "/help-advice?topic=Finishes Lacquer"
  },
  {
    "name": "Finishes Hard Wax Oil",
    "url": "/help-advice?topic=Finishes Hard Wax Oil"
  },
  {
    "name": "Staining Wood",
    "url": "/help-advice?topic=Staining Wood"
  },
  {
    "name": "Subfloor",
    "url": "/help-advice?topic=Subfloor"
  },
  {
    "name": "Under Floor Heating",
    "url": "/help-advice?topic=Under Floor Heating"
  },
  {
    "name": "Floor Damage",
    "url": "/help-advice?topic=Floor Damage"
  },
  {
    "name": "Underlay",
    "url": "/help-advice?topic=Underlay"
  },
  {
    "name": "Regulations",
    "url": "/help-advice?topic=Regulations"
  },
  {
    "name": "Moisture",
    "url": "/help-advice?topic=Moisture"
  },
  {
    "name": "Floor Fitting",
    "url": "/help-advice?topic=Floor Fitting"
  },
  {
    "name": "Adhesives",
    "url": "/help-advice?topic=Adhesives"
  },
  {
    "name": "Abrasives",
    "url": "/help-advice?topic=Abrasives"
  },
  {
    "name": "Fillers",
    "url": "/help-advice?topic=Fillers"
  },
  {
    "name": "Sanding Machines",
    "url": "/help-advice?topic=Sanding Machines"
  }
]

data.faqs = faqs
data.faq_filters = faq_filters
data.search = search
data.total_faqs = len(faqs)
data.user = frappe.session.user
data.metatags = {
    "og:type": "website"
}