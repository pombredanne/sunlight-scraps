require 'rubygems'
require 'nokogiri'
require 'open-uri'
require 'csv'
require 'cgi'

module OpenGov
  
  DOMAIN = "http://opengov.ideascale.com"
  BASE_URL = "http://opengov.ideascale.com/akira/ideafactory.do"
  
  def self.save_summary
    results = generate_summary
    filename = "_output/summary.csv"
    out_file = File.open(filename, 'w')
    
    lookup_label = category_ids_and_labels
    CSV::Writer.generate(out_file) do |csv|
      csv << [
        "category_id",
        "category_label",
        "votes_count",
        "votes_min",
        "votes_avg",
        "votes_max",
      ]
      results.each do |key, value|
        csv << [
          key,
          lookup_label[key],
          value[:count],
          value[:min],
          value[:avg],
          value[:max],
        ]
      end
    end
    out_file.close
    puts "----------"
    puts "Done"
  end
  
  def self.generate_summary
    result = {}
    categories.each do |item|
      puts "==== Category %i ====" % item[:id]
      url = item[:url]
      filename = "_output/%i.csv" % item[:id]
      data = generic_load(url)
      votes = extract_votes(data)
      result[item[:id]] = generate_statistics(votes)
    end
    result
  end
  
  def self.extract_votes(data)
    data.map { |i| i[:vote].to_i }
  end
  
  def self.generate_statistics(votes)
    sum = votes.reduce { |acc, i| acc + i }
    len = votes.length
    {
      :count => len,
      :min   => votes.min,
      :max   => votes.max,
      :sum   => sum,
      :avg   => (1.0 * sum) / len,
      :items => votes.sort
    }
  end
  
  def self.save_all
    page = "%s?mode=recent" % BASE_URL
    filename = '_output/all.csv'
    generic_save(page, filename)
  end
  
  def self.save_categories
    categories.each do |item|
      puts "==== Category %i ====" % item[:id]
      filename = "_output/%i.csv" % item[:id]
      generic_save(item[:url], filename)
    end
  end
  
  # Note: generic_save and generic_load are similar.
  # Therefore, common code should be factored out.
  def self.generic_save(start_url, filename)
    page = start_url.dup
    out_file = File.open(filename, 'w')
    CSV::Writer.generate(out_file) do |csv|
      while true
        puts "%s" % page
        doc = Nokogiri::HTML(grab(page))
        results = doc.css('div#TopicListOnly > table > tr')
        puts "    %i items" % results.length
        results.each do |result|
          vote_node_set = result.search('div#IdeaScale_Vote > div > a')
          vote = vote_node_set[1].text
          title_node_set = result.search('div#IdeaScale_IdeaTitle > a > span')
          title = title_node_set[0].text
          csv << [ vote, title ]
        end
        page = url_for_next_page(doc)
        unless page
          puts "That's all folks."
          break
        end
      end
    end
    out_file.close
  end
  
  # loads into memory
  # 
  # Note: generic_save and generic_load are similar.
  # Therefore, common code should be factored out.
  def self.generic_load(start_url)
    page = start_url.dup
    data = []
    while true
      puts "%s" % page
      doc = Nokogiri::HTML(grab(page))
      results = doc.css('div#TopicListOnly > table > tr')
      puts "    %i items" % results.length
      results.each do |result|
        vote_node_set = result.search('div#IdeaScale_Vote > div > a')
        vote = vote_node_set[1].text
        title_node_set = result.search('div#IdeaScale_IdeaTitle > a > span')
        title = title_node_set[0].text
        data << {
          :vote  => vote,
          :title => title
        }
      end
      page = url_for_next_page(doc)
      unless page
        puts "That's all folks."
        break
      end
    end
    data
  end
  
  def self.retrieve_categories
    page = BASE_URL
    doc = Nokogiri::HTML(grab(page))
    
  end
  
  def self.url_for_next_page(doc)
    results = doc.css("div.pages > a.nextprev")
    nodes = []
    case results.length
    when 0:
      return nil
    when 1:
      nodes << results[0]
    when 2:
      nodes << results[1] << results[0]
    else
      raise "Bad parse.  Expecting length of 0, 1, or 2.  Got %s." % n
    end
    
    nodes.each do |node|
      if next?(node)
        path = node.get_attribute("href")
        return(DOMAIN + path)
      end
    end
    puts "No link found for the next page."
    return nil
  end
  
  def self.next?(node)
    if node.text.match(/next/i)
      return true
    else
      return false
    end
  end
      
  def self.categories
    base_url = "http://opengov.ideascale.com/akira/ideafactory.do"
    category_ids.map do |category_id|
      {
        :id    => category_id,
        :url   => "%s?discussionID=%s" % [base_url, category_id],
        :label => category_ids_and_labels[category_id]
      }
    end
  end

  # Category IDs from:
  # http://opengov.ideascale.com/akira/ideafactory.do
  #
  # * All (1135)
  # * 1. Transparency
  #       o Making Data More Accessible (108)
  #       o Making Government Operations More Open (182)
  #       o Records Management (46)
  # * 2. Participation
  #       o New Strategies and Techniques (164)
  #       o New Tools and Technologies (72)
  #       o Federal Advisory Committees (15)
  #       o Rulemaking (33)
  # * 3. Collaboration
  #       o Between Federal Agencies (21)
  #       o Between Federal, State, and Local Governments (46)
  #       o Public-Private Partnerships (37)
  #       o Do-It-Yourself Government (13)
  # * 4. Capacity Building
  #       o Hiring & Recruitment (24)
  #       o Performance Appraisal (21)
  #       o Training and Development (41)
  #       o Communications Strategies (23)
  #       o Strategic Planning and Budgeting (34)
  # * 5. Legal & Policy Challenges
  #       o Legal & Policy Challenges (146)
  # * Uncategorized
  #       o Uncategorized (109)
  
  def self.category_ids_and_labels
    {
      2236 => "Transparency : Making Data More Accessible",
      2237 => "Transparency : Making Government Operations More Open",
      2238 => "Transparency : Records Management",

      2242 => "Participation : New Strategies and Techniques",
      2243 => "Participation : New Tools and Technologies",
      2244 => "Participation : Federal Advisory Committees",
      2245 => "Participation : Rulemaking",

      2246 => "Collaboration : Between Federal Agencies",
      2247 => "Collaboration : Between Federal, State, and Local Governments",
      2248 => "Collaboration : Public-Private Partnerships",
      2249 => "Collaboration : Do-It-Yourself Government",

      2250 => "Capacity Building : Hiring & Recruitment",
      2251 => "Capacity Building : Performance Appraisal",
      2252 => "Capacity Building : Training and Development",
      2253 => "Capacity Building : Communications Strategies",
      2254 => "Capacity Building : Strategic Planning and Budgeting",

      2294 => "Legal & Policy Challenges",
      2255 => "Uncategorized",
    }
  end

  def self.category_ids
    category_ids_and_labels.keys
  end
  
  def self.filter_invalid_chars(content)
    content.gsub(%r{\0}, "")
  end

  # Uses cache if it can
  def self.grab(url)
    filename = "_cache/%s" % CGI.escape(url)
    content = ""
    if File.exist?(filename)
      f = File.open(filename, "r")
      content = f.read
      f.close
    else
      puts "Fetching %s" % url
      sleep(0.25)
      stream = open(url)
      content = stream.read
      stream.close
      puts "Writing %s" % filename
      f = File.open(filename, "w")
      f.write(content)
      f.close
    end
    filter_invalid_chars(content)
  end

end

OpenGov.save_summary
