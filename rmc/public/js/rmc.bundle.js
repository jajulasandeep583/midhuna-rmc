// Shared desk helpers for RMC.
//
// The one thing every screen needs is the same: "show me yesterday", "show me
// this month". Typing two dates for that is the fastest way to make a plant
// manager stop using a report, so every board and every report gets the same
// Period picker, and the two date fields stay there for anything custom.

frappe.provide("rmc");

rmc.PERIODS = [
	"Today",
	"Yesterday",
	"This Week",
	"Last 7 Days",
	"This Month",
	"Last Month",
	"Last 30 Days",
	"Last 90 Days",
	"This Quarter",
	"This Year",
	"Custom",
];

// -> [from, to] as yyyy-mm-dd strings
rmc.period_range = function (period) {
	const D = frappe.datetime;
	const today = D.get_today();
	const month_start = D.month_start();

	switch (period) {
		case "Today":
			return [today, today];
		case "Yesterday": {
			const y = D.add_days(today, -1);
			return [y, y];
		}
		case "This Week":
			return [D.week_start(), today];
		case "Last 7 Days":
			return [D.add_days(today, -6), today];
		case "This Month":
			return [month_start, today];
		case "Last Month": {
			const start = D.add_months(month_start, -1);
			return [start, D.add_days(month_start, -1)];
		}
		case "Last 30 Days":
			return [D.add_days(today, -29), today];
		case "Last 90 Days":
			return [D.add_days(today, -89), today];
		case "This Quarter": {
			const m = new Date(today).getMonth();          // 0-11
			const qstart = D.add_months(D.year_start(), Math.floor(m / 3) * 3);
			return [qstart, today];
		}
		case "This Year":
			return [D.year_start(), today];
		default:
			return null;                                    // Custom: leave the dates alone
	}
};

// Filter definition for a Query/Script Report. Drop it in front of from_date
// and to_date and the three stay in step.
rmc.period_filter = function (default_period) {
	return {
		fieldname: "period",
		label: __("Period"),
		fieldtype: "Select",
		options: rmc.PERIODS.join("\n"),
		default: default_period || "Last 30 Days",
		on_change: function () {
			const p = frappe.query_report.get_filter_value("period");
			const range = rmc.period_range(p);
			if (!range) return;                             // Custom
			frappe.query_report.set_filter_value({ from_date: range[0], to_date: range[1] });
		},
	};
};

// Same control for a desk page. Returns the three fields; call get_range() to
// read the dates whichever way the user set them.
rmc.add_period_fields = function (page, on_change, default_period) {
	const period = page.add_field({
		fieldtype: "Select",
		fieldname: "period",
		label: __("Period"),
		options: rmc.PERIODS,
		default: default_period || "Last 7 Days",
		change: () => {
			const range = rmc.period_range(period.get_value());
			if (range) {
				from.set_value(range[0]);
				to.set_value(range[1]);
			}
			on_change();
		},
	});
	const initial = rmc.period_range(default_period || "Last 7 Days") ||
		[frappe.datetime.add_days(frappe.datetime.get_today(), -6), frappe.datetime.get_today()];
	const from = page.add_field({
		fieldtype: "Date", fieldname: "from_date", label: __("From"),
		default: initial[0],
		change: () => { period.set_value("Custom"); on_change(); },
	});
	const to = page.add_field({
		fieldtype: "Date", fieldname: "to_date", label: __("To"),
		default: initial[1],
		change: () => { period.set_value("Custom"); on_change(); },
	});
	return {
		period, from, to,
		get_range: () => [from.get_value(), to.get_value()],
	};
};
