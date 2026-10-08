# Sponsor-side. Students: you do not need to run this, and cannot; it reads Corridor's database.
# It wrote matterport_tours.csv: the public, active Matterport tours Corridor holds for the corridor
# organization. Run from a Corridor checkout:
#   OUT=matterport_tours.csv bin/prod-run bin/export_matterport_tours.rb   (read-only)
# Read-only. The public, active Matterport tours Corridor holds for the corridor org.
require "csv"
OUT = ENV.fetch("OUT")
tours = MatterportTour.unscoped.where(organization_id: 1, visibility: "public", state: "active")
props = Property.unscoped.where(id: tours.map(&:property_id)).index_by(&:id)
rows = tours.map do |t|
  p = props[t.property_id]
  [t.id, t.property_id, p&.address.to_s, t.label.to_s, t.scan_date&.to_s, t.floors, t.rooms, t.is_primary ? "true" : "false", t.model_id, t.share_url]
end.sort_by { |r| [r[2], r[7] == "true" ? 0 : 1, r[0]] }
CSV.open(OUT, "w") do |csv|
  csv << %w[id property_id address label scan_date floors rooms is_primary model_id share_url]
  rows.each { |r| csv << r }
end
$stderr.puts "tours=#{rows.size} properties=#{rows.map { |r| r[1] }.uniq.size}"
