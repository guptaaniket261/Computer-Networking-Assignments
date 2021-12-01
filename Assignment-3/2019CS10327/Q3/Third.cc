#include <fstream>
#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"

#include <iostream>
#include <fstream>
#include <string>

using namespace ns3;

class MyApp : public Application 
{
public:

  MyApp ();
  virtual ~MyApp();

  void Setup (Ptr<Socket> socket, Address address, uint32_t packetSize, uint32_t nPackets, DataRate dataRate);

private:
  virtual void StartApplication (void);
  virtual void StopApplication (void);

  void ScheduleTx (void);
  void SendPacket (void);

  Ptr<Socket>     m_socket;
  Address         m_peer;
  uint32_t        m_packetSize;
  uint32_t        m_nPackets;
  DataRate        m_dataRate;
  EventId         m_sendEvent;
  bool            m_running;
  uint32_t        m_packetsSent;
};

MyApp::MyApp ()
  : m_socket (0), 
    m_peer (), 
    m_packetSize (0), 
    m_nPackets (0), 
    m_dataRate (0), 
    m_sendEvent (), 
    m_running (false), 
    m_packetsSent (0)
{
}

MyApp::~MyApp()
{
  m_socket = 0;
}

void
MyApp::Setup (Ptr<Socket> socket, Address address, uint32_t packetSize, uint32_t nPackets, DataRate dataRate)
{
  m_socket = socket;
  m_peer = address;
  m_packetSize = packetSize;
  m_nPackets = nPackets;
  m_dataRate = dataRate;
}

void
MyApp::StartApplication (void)
{
  m_running = true;
  m_packetsSent = 0;
  m_socket->Bind ();
  m_socket->Connect (m_peer);
  SendPacket ();
}

void 
MyApp::StopApplication (void)
{
  m_running = false;

  if (m_sendEvent.IsRunning ())
    {
      Simulator::Cancel (m_sendEvent);
    }

  if (m_socket)
    {
      m_socket->Close ();
    }
}

void 
MyApp::SendPacket (void)
{
  Ptr<Packet> packet = Create<Packet> (m_packetSize);
  m_socket->Send (packet);

  if (++m_packetsSent < m_nPackets)
    {
      ScheduleTx ();
    }
}

void 
MyApp::ScheduleTx (void)
{
  if (m_running)
    {
      Time tNext (Seconds (m_packetSize * 8 / static_cast<double> (m_dataRate.GetBitRate ())));
      m_sendEvent = Simulator::Schedule (tNext, &MyApp::SendPacket, this);
    }
}

static void
CwndChange (Ptr<OutputStreamWrapper> stream, uint32_t oldCwnd, uint32_t newCwnd)
{
  NS_LOG_UNCOND (Simulator::Now ().GetSeconds () << "\t" << newCwnd);
  *stream->GetStream () << Simulator::Now ().GetSeconds () << "\t" << oldCwnd << "\t" << newCwnd << std::endl;
}

static void
RxDrop (Ptr<PcapFileWrapper> file, Ptr<const Packet> p)
{
  NS_LOG_UNCOND ("RxDrop at " << Simulator::Now ().GetSeconds ());
  file->Write (Simulator::Now (), p);
}

int 
main (int argc, char *argv[])
{

  CommandLine cmd;
  cmd.Parse (argc, argv);
  int configuration = 1;
  std::string cwndFileName1 = "connection1_config1.cwnd";
  std::string cwndFileName2 = "connection2_config1.cwnd";
  std::string cwndFileName3 = "connection3_config1.cwnd";
  std::string pckDropFileName1 = "config1_1.pcap";
  std::string pckDropFileName2 = "config1_2.pcap";

  if (argc>1){
      std::string configuration_str = argv[1];
      if (configuration_str == "1") configuration = 1;
      if (configuration_str == "2") configuration = 2;
      if (configuration_str == "3") configuration = 3;

      
      cwndFileName1 = "connection1_config"+configuration_str+".cwnd";
      cwndFileName2 = "connection2_config"+configuration_str+".cwnd";
      cwndFileName3 = "connection3_config"+configuration_str+".cwnd";
      pckDropFileName1 = "config"+configuration_str+"_1.pcap";
      pckDropFileName2 = "config"+configuration_str+"_2.pcap";
  }
  
  NodeContainer nodes1;
  NodeContainer nodes2;
  nodes1.Create(2);
  nodes2.Create(1);
  nodes2.Add(nodes1.Get(1));

  PointToPointHelper pointToPoint1;
  PointToPointHelper pointToPoint2;

  pointToPoint1.SetDeviceAttribute ("DataRate", StringValue ("10Mbps"));
  pointToPoint1.SetChannelAttribute ("Delay", StringValue ("3ms"));

  pointToPoint2.SetDeviceAttribute ("DataRate", StringValue ("9Mbps"));
  pointToPoint2.SetChannelAttribute ("Delay", StringValue ("3ms"));

  NetDeviceContainer devices1, devices2;
  devices1 = pointToPoint1.Install (nodes1);
  devices2 = pointToPoint2.Install (nodes2);

  Ptr<RateErrorModel> em1 = CreateObject<RateErrorModel> ();
  Ptr<RateErrorModel> em2 = CreateObject<RateErrorModel> ();
  em1->SetAttribute ("ErrorRate", DoubleValue (0.00001));
  em2->SetAttribute ("ErrorRate", DoubleValue (0.00001));
  devices1.Get (1)->SetAttribute ("ReceiveErrorModel", PointerValue (em1));
  devices2.Get (1)->SetAttribute ("ReceiveErrorModel", PointerValue (em2));

  InternetStackHelper stack;
  stack.Install (nodes1);
  stack.Install (nodes2.Get(0));

  Ipv4AddressHelper address1;
  address1.SetBase ("10.1.1.0", "255.255.255.0");
  Ipv4InterfaceContainer interfaces1 = address1.Assign (devices1);

  Ipv4AddressHelper address2;
  address2.SetBase ("10.1.2.0", "255.255.255.0");
  Ipv4InterfaceContainer interfaces2 = address2.Assign (devices2);

  uint16_t sinkPort1 = 8080;
  uint16_t sinkPort2 = 8085;
  uint16_t sinkPort3 = 8090;

  Address sinkAddress1 (InetSocketAddress (interfaces1.GetAddress (1), sinkPort1));
  Address sinkAddress2 (InetSocketAddress (interfaces1.GetAddress (1), sinkPort2));
  Address sinkAddress3 (InetSocketAddress (interfaces2.GetAddress (1), sinkPort3));

  PacketSinkHelper packetSinkHelper1 ("ns3::TcpSocketFactory", InetSocketAddress (Ipv4Address::GetAny (), sinkPort1));
  PacketSinkHelper packetSinkHelper2 ("ns3::TcpSocketFactory", InetSocketAddress (Ipv4Address::GetAny (), sinkPort2));
  PacketSinkHelper packetSinkHelper3 ("ns3::TcpSocketFactory", InetSocketAddress (Ipv4Address::GetAny (), sinkPort3));

  ApplicationContainer sinkApp1 = packetSinkHelper1.Install (nodes1.Get (1));
  ApplicationContainer sinkApp2 = packetSinkHelper2.Install (nodes1.Get (1));
  ApplicationContainer sinkApp3 = packetSinkHelper3.Install (nodes1.Get (1));
  
  sinkApp1.Start (Seconds (0.));
  sinkApp1.Stop (Seconds (30.));
  sinkApp2.Start (Seconds (0.));
  sinkApp2.Stop (Seconds (30.));
  sinkApp3.Start (Seconds (0.));
  sinkApp3.Stop (Seconds (30.));

  TypeId tid12 = TypeId::LookupByName ("ns3::TcpNewReno");
  TypeId tid3 = TypeId::LookupByName ("ns3::TcpNewReno");
  if(configuration == 2){
    tid3 = TypeId::LookupByName ("ns3::TcpNewRenoCSE");
  }
  if(configuration == 3){
    tid12 = TypeId::LookupByName ("ns3::TcpNewRenoCSE");
    tid3 = TypeId::LookupByName ("ns3::TcpNewRenoCSE");
  }

  std::stringstream nodeId12, nodeId3;
  nodeId12 << nodes1.Get (0)->GetId ();
  std::string specificNode1 = "/NodeList/"+nodeId12.str()+"/$ns3::TcpL4Protocol/SocketType";
  Config::Set (specificNode1, TypeIdValue (tid12));
  
  nodeId3 << nodes2.Get (0)->GetId ();
  std::string specificNode2 = "/NodeList/"+nodeId3.str()+"/$ns3::TcpL4Protocol/SocketType";
  Config::Set (specificNode2, TypeIdValue (tid3));
  
  Ptr<Socket> ns3TcpSocket1 = Socket::CreateSocket (nodes1.Get (0), TcpSocketFactory::GetTypeId ());
  Ptr<Socket> ns3TcpSocket2 = Socket::CreateSocket (nodes1.Get (0), TcpSocketFactory::GetTypeId ());
  Ptr<Socket> ns3TcpSocket3 = Socket::CreateSocket (nodes2.Get (0), TcpSocketFactory::GetTypeId ());

  // ns3TcpSocket1->TraceConnectWithoutContext ("CongestionWindow", MakeCallback (&CwndChange1));
  // ns3TcpSocket2->TraceConnectWithoutContext ("CongestionWindow", MakeCallback (&CwndChange2));
  // ns3TcpSocket3->TraceConnectWithoutContext ("CongestionWindow", MakeCallback (&CwndChange3));

  Ptr<MyApp> app1 = CreateObject<MyApp> ();
  Ptr<MyApp> app2 = CreateObject<MyApp> ();
  Ptr<MyApp> app3 = CreateObject<MyApp> ();
  app1->Setup (ns3TcpSocket1, sinkAddress1, 3000, 40000, DataRate ("1.5Mbps"));
  app2->Setup (ns3TcpSocket2, sinkAddress2, 3000, 40000, DataRate ("1.5Mbps"));
  app3->Setup (ns3TcpSocket3, sinkAddress3, 3000, 40000, DataRate ("1.5Mbps"));

  nodes1.Get (0)->AddApplication (app1);
  nodes1.Get (0)->AddApplication (app2);
  nodes2.Get (0)->AddApplication (app3);

  app1->SetStartTime (Seconds (1.));
  app1->SetStopTime (Seconds (20.));
  app2->SetStartTime (Seconds (5.));
  app2->SetStopTime (Seconds (25.));
  app3->SetStartTime (Seconds (15.));
  app3->SetStopTime (Seconds (30.));

  AsciiTraceHelper asciiTraceHelper;
  Ptr<OutputStreamWrapper> stream1 = asciiTraceHelper.CreateFileStream (cwndFileName1);
  Ptr<OutputStreamWrapper> stream2 = asciiTraceHelper.CreateFileStream (cwndFileName2);
  Ptr<OutputStreamWrapper> stream3 = asciiTraceHelper.CreateFileStream (cwndFileName3);

  ns3TcpSocket1->TraceConnectWithoutContext ("CongestionWindow", MakeBoundCallback (&CwndChange, stream1));
  ns3TcpSocket2->TraceConnectWithoutContext ("CongestionWindow", MakeBoundCallback (&CwndChange, stream2));
  ns3TcpSocket3->TraceConnectWithoutContext ("CongestionWindow", MakeBoundCallback (&CwndChange, stream3));


  PcapHelper pcapHelper;
  Ptr<PcapFileWrapper> file1 = pcapHelper.CreateFile (pckDropFileName1, std::ios::out, PcapHelper::DLT_PPP);
  Ptr<PcapFileWrapper> file2 = pcapHelper.CreateFile (pckDropFileName2, std::ios::out, PcapHelper::DLT_PPP);

  devices1.Get (1)->TraceConnectWithoutContext ("PhyRxDrop", MakeBoundCallback (&RxDrop, file1));
  devices2.Get (1)->TraceConnectWithoutContext ("PhyRxDrop", MakeBoundCallback (&RxDrop, file2));

//   devices.Get (1)->TraceConnectWithoutContext ("PhyRxDrop", MakeCallback (&RxDrop));

  Simulator::Stop (Seconds (32.));
  Simulator::Run ();
  Simulator::Destroy ();

  return 0;
}

